import uuid
from modules import diagnostico
from modules import limpeza
from modules import otimizacao
from modules import servicos
from modules import logs
from modules import relatorio
from modules.gui.jobs import JobManager


import logging
from modules.core.gui_logger import GUILogger

class PhoenixAPI:
    """
    Ponte entre o front-end (HTML/JS) e o núcleo de funcionalidades do Phoenix.
    Cada método retorna dados em formas simples (dict/list/str) que o
    pywebview serializa automaticamente para JSON no lado do JavaScript.
    """

    def __init__(self, hw_info: dict, job_manager=None, hardware_service=None, window_controller=None, routine_service=None):
        self._hw_info = hw_info
        self._id_atendimento = None
        self._nome_cliente = ""
        self._job_manager = job_manager or JobManager(on_terminal_state=GUILogger.log_job_terminal_state)

        if hardware_service is None:
            from modules.core.hardware_service import HardwareService
            hardware_service = HardwareService(hw_info=hw_info)
        self._hardware_service = hardware_service

        if window_controller is None:
            from modules.gui.window_controller import WindowController
            window_controller = WindowController()
        self._window_controller = window_controller

        if routine_service is None:
            from modules.core.routine_service import RoutineService
            routine_service = RoutineService()
        self._routine_service = routine_service
        self._protection_state = "not_attempted"
        self._restore_attempt_failed = False
        
        GUILogger.setup()

    def _iniciar_job(self, target_fn, *args, operation_name="unknown", exclusive_group=None, timeout=None, pass_job_context=False, **kwargs) -> dict:
        """Delega a criação do job para o JobManager e retorna o formato esperado pelo JS."""
        if timeout is None:
            if operation_name == "rotina_completa":
                timeout = 600
            elif operation_name == "criar_ponto_restauracao":
                timeout = 300
            elif operation_name == "otimizar_disco":
                timeout = 300
            elif exclusive_group == "system_mutation":
                timeout = 180
            elif operation_name in ("carregar_hardware_cache", "iniciar_atualizacao", "forcar_rescan_hardware"):
                timeout = 45
            else:
                timeout = 30

        job_id = self._job_manager.submit(
            target_fn,
            *args,
            operation_name=operation_name,
            exclusive_group=exclusive_group,
            timeout=timeout,
            pass_job_context=pass_job_context,
            **kwargs
        )
        return {"job_id": job_id}

    def verificar_tarefa(self, job_id: str) -> dict:
        """Retorna o status atual de uma tarefa a partir do JobManager."""
        return self._job_manager.consultar(job_id)

    def cancelar_tarefa(self, job_id: str) -> dict:
        """Solicita o cancelamento cooperativo de uma tarefa."""
        return self._job_manager.cancelar(job_id)

    # ---------- Hardware / contexto inicial ----------

    def obter_hardware(self) -> dict:
        """Legado/Compatibilidade: Retorna o hardware já detectado pelo launcher."""
        return self._hardware_service.obter_hardware()

    def obter_inventario_atual(self) -> dict:
        """Retorna o contrato estático do hardware atual."""
        return self._hardware_service.obter_hardware()

    def obter_estado_coleta(self) -> dict:
        """Retorna o status da coleta (completo, parcial, falhou, etc)."""
        hw = self._hardware_service.obter_hardware()
        return {
            "status": hw.get("status", "nao_carregado"),
            "avisos": hw.get("avisos", []),
            "coletado_em": hw.get("coletado_em")
        }

    def obter_nivel_qualidade_visual(self) -> str:
        """
        Retorna 'alto', 'medio' ou 'baixo' para o front-end ajustar automaticamente
        a intensidade dos efeitos visuais (glassmorphism, partículas, blur).
        """
        return self._hardware_service.obter_nivel_qualidade_visual()

    # ---------- Atendimento ----------

    def _make_error(self, codigo: str) -> dict:
        mensagens = {
            "INVALID_CLIENT_NAME": "O nome do cliente é inválido ou está vazio.",
            "INVALID_CLIENT_ID": "O ID do cliente fornecido é inválido.",
            "CLIENT_NOT_FOUND": "O cliente especificado não pôde ser encontrado.",
            "CLIENT_CREATE_FAILED": "Falha ao criar o diretório do cliente portátil.",
            "CLIENT_SELECT_FAILED": "Falha ao selecionar e definir o cliente ativo.",
            "CLIENT_DELETE_FAILED": "Falha ao remover os dados do cliente.",
            "CLIENT_DELETE_FAILED_PERMISSION": "Permissão negada ao tentar remover o cliente.",
            "PORTABLE_MODE_REQUIRED": "Esta ação exige que o modo Portable esteja ativo.",
            "PERSISTENCE_WRITE_FAILED": "Falha ao salvar de forma segura os metadados do cliente."
        }
        erro_str = mensagens.get(codigo)
        if not erro_str:
            import logging
            logging.warning(f"Unknown portable API error code intercepted: {codigo}")
            codigo = "UNKNOWN_ERROR"
            erro_str = "Ocorreu um erro interno desconhecido na operação do cliente portátil."

        return {
            "ok": False,
            "codigo": codigo,
            "erro": erro_str
        }

    def iniciar_atendimento(self, nome_cliente: str = "") -> dict:
        self._nome_cliente = nome_cliente or ""
        self._id_atendimento = logs.gerar_id_atendimento()
        return {"id_atendimento": self._id_atendimento}

    def obter_clientes_portable(self) -> dict:
        """Lista clientes salvos no pen drive (modo portable)."""
        from modules.shared import IS_PORTABLE, listar_clientes_portable
        if not IS_PORTABLE:
            erro = self._make_error("PORTABLE_MODE_REQUIRED")
            erro["portable"] = False
            return erro
        return {
            "ok": True,
            "portable": True,
            "clientes": listar_clientes_portable()
        }

    def criar_cliente_portable(self, nome: str) -> dict:
        from modules.shared import criar_cliente_portable, IS_PORTABLE
        if not IS_PORTABLE:
            return self._make_error("PORTABLE_MODE_REQUIRED")
        if not nome or not nome.strip():
            return self._make_error("INVALID_CLIENT_NAME")

        try:
            res = criar_cliente_portable(nome)
            if not res.get("ok"):
                return self._make_error(res.get("erro", "CLIENT_CREATE_FAILED"))
            return {"ok": True, "cliente": res["cliente"]}
        except Exception:
            return self._make_error("CLIENT_CREATE_FAILED")

    def selecionar_cliente(self, id_cliente: str) -> dict:
        """Define o cliente ativo da sessão."""
        from modules.shared import selecionar_cliente_portable, IS_PORTABLE

        if not id_cliente or not id_cliente.strip():
            return self._make_error("INVALID_CLIENT_ID")

        res = selecionar_cliente_portable(id_cliente.strip())
        if not res.get("ok"):
            return self._make_error(res.get("erro", "CLIENT_SELECT_FAILED"))

        return res

    def remover_cliente_portable(self, id_cliente: str) -> dict:
        """Remove um cliente do pen drive."""
        from modules.shared import remover_cliente_portable, IS_PORTABLE
        if not IS_PORTABLE:
            return self._make_error("PORTABLE_MODE_REQUIRED")
        res = remover_cliente_portable(id_cliente)
        if not res.get("ok"):
            return self._make_error(res.get("erro", "CLIENT_DELETE_FAILED"))
        return {"ok": True}

    def obter_modo_portable(self) -> dict:
        from modules.shared import IS_PORTABLE, CLIENTE_ATIVO_ID, CLIENTE_ATIVO_NOME
        return {
            "portable": IS_PORTABLE,
            "cliente_ativo": {"id": CLIENTE_ATIVO_ID, "nome": CLIENTE_ATIVO_NOME} if CLIENTE_ATIVO_ID else None
        }

    # ---------- Diagnóstico ----------

    def obter_diagnostico(self) -> dict:
        """Coleta diagnóstico completo em segundo plano para exibir na GUI (fire-and-forget)."""
        return self._iniciar_job(
            lambda: {"ok": True, "dados": diagnostico.coletar_diagnostico_silencioso()},
            operation_name="obter_diagnostico"
        )

    def obter_metricas_rapidas(self) -> dict:
        """Retorna CPU% e RAM% instantâneos sem bloquear. Uso: polling de tempo real na GUI."""
        return self._hardware_service.obter_metricas_rapidas()

    def obter_info_sistema_detalhado(self) -> dict:
        return self._hardware_service.obter_info_sistema_detalhado()

    def obter_metricas_completas(self) -> dict:
        return self._hardware_service.obter_metricas_completas()

    def obter_gpu_rapida(self) -> dict:
        """Retorna métricas rápidas da GPU primária (uso, temp, VRAM)."""
        return self._hardware_service.obter_gpu_rapida()

    # ---------- Limpeza ----------

    def executar_limpeza(self) -> dict:
        """Executa limpeza completa em segundo plano com progresso detalhado."""
        def worker(job_context):
            from modules.core.cleanup_service import executar_limpeza as do_limpeza
            
            def prog_cb(mensagem, progresso, detalhes):
                job_context.update_progress(progresso, msg=mensagem, details=detalhes)
                
            res = do_limpeza(
                progress_callback=prog_cb,
                cancel_event=job_context.cancel_event,
                incluir_lixeira=False
            )
            
            if self._id_atendimento:
                from modules import logs
                logs.registrar_acao(self._id_atendimento, "Limpeza executada", f"{res['espaco_liberado_mb']} MB liberados")
                
            return res
            
        return self._iniciar_job(
            worker,
            operation_name="executar_limpeza",
            exclusive_group="system_mutation",
            pass_job_context=True,
            timeout=900.0
        )

    # ---------- Otimização ----------

    def criar_ponto_restauracao(self) -> dict:
        """Cria um ponto de restauração em segundo plano (fire-and-forget)."""
        self._protection_state = "not_attempted"
        self._restore_attempt_failed = False
        def worker(job_context):
            res = otimizacao.criar_ponto_restauracao(cancel_event=job_context.cancel_event)
            if res.get("codigo") == "COMMAND_CANCELLED":
                from modules.core.exceptions import JobCancelledError
                raise JobCancelledError()
            if res.get("ok"):
                self._protection_state = "restore_created"
            else:
                self._restore_attempt_failed = True
            return res
        return self._iniciar_job(
            worker,
            operation_name="criar_ponto_restauracao",
            exclusive_group="system_mutation",
            pass_job_context=True
        )

    def carregar_hardware_cache(self) -> dict:
        """Carrega hardware do cache ou refaz scan (fire-and-forget). Alias de iniciar_atualizacao."""
        return self.iniciar_atualizacao()

    def iniciar_atualizacao(self) -> dict:
        job_id = str(uuid.uuid4())

        def prog_cb(msg):
            pct = self._job_manager.get_progress(job_id)
            if "WMI" in msg or "CIM" in msg: pct = 33
            elif "cache" in msg: pct = 66
            elif "Final" in msg: pct = 100
            self._job_manager.update_progress(job_id, pct, msg)

        def worker():
            return self._hardware_service.carregar_hardware_cache(progress_callback=prog_cb)

        self._iniciar_job(worker, job_id=job_id, operation_name="iniciar_atualizacao")
        self._job_manager.update_progress(job_id, 0, "Iniciando detecção...")
        return {"job_id": job_id}

    def forcar_rescan_hardware(self) -> dict:
        """Força um scan completo de hardware (fire-and-forget)."""
        job_id = str(uuid.uuid4())
        
        def prog_cb(msg):
            pct = self._job_manager.get_progress(job_id)
            if "WMI" in msg or "CIM" in msg: pct = 33
            elif "cache" in msg: pct = 66
            elif "Final" in msg: pct = 100
            self._job_manager.update_progress(job_id, pct, msg)

        def worker():
            return self._hardware_service.forcar_rescan_hardware(progress_callback=prog_cb)
            
        self._iniciar_job(worker, job_id=job_id, operation_name="forcar_rescan_hardware")
        self._job_manager.update_progress(job_id, 0, "Iniciando detecção forçada...")
        return {"job_id": job_id}

    def confirmar_risco_protecao(self) -> dict:
        if self._restore_attempt_failed:
            self._protection_state = "risk_accepted"
            return {"ok": True}
        return {"ok": False, "erro": "Não é possível confirmar risco sem uma falha prévia de restauração.", "codigo": "INVALID_RISK_ACCEPTANCE"}

    def _require_protection(self):
        if self._protection_state not in ("restore_created", "risk_accepted"):
            from modules.core.exceptions import ProtectionError
            raise ProtectionError("Operação bloqueada: O sistema não está protegido. Execute criar_ponto_restauracao antes.")

    def executar_otimizacao_geral(self) -> dict:
        """Aplica otimizações gerais em segundo plano (fire-and-forget)."""
        def acao(job_context):
            self._require_protection()
            res = otimizacao.executar_otimizacao_geral(self._id_atendimento, cancel_event=job_context.cancel_event)
            if res.get("codigo") == "COMMAND_CANCELLED":
                from modules.core.exceptions import JobCancelledError
                raise JobCancelledError()
            return res
        return self._iniciar_job(acao, operation_name="otimizacao_geral", exclusive_group="system_mutation", pass_job_context=True)

    def executar_otimizacao_gaming(self, resetar_rede: bool = False) -> dict:
        """Aplica otimizações para jogos em segundo plano (fire-and-forget)."""
        def acao(job_context):
            self._require_protection()
            res = otimizacao.executar_otimizacao_gaming(self._id_atendimento, resetar_rede=resetar_rede, cancel_event=job_context.cancel_event)
            if res.get("codigo") == "COMMAND_CANCELLED":
                from modules.core.exceptions import JobCancelledError
                raise JobCancelledError()
            return res
        return self._iniciar_job(acao, operation_name="otimizacao_gaming", exclusive_group="system_mutation", pass_job_context=True)

    def otimizar_disco(self) -> dict:
        """Otimiza o disco em segundo plano (fire-and-forget)."""
        def worker(job_context):
            res = otimizacao.otimizar_disco_principal(cancel_event=job_context.cancel_event)
            if res.get("codigo") == "COMMAND_CANCELLED":
                from modules.core.exceptions import JobCancelledError
                raise JobCancelledError()
            return res
        return self._iniciar_job(
            worker,
            operation_name="otimizar_disco",
            exclusive_group="system_mutation",
            pass_job_context=True
        )

    def listar_inicializacao(self) -> dict:
        return otimizacao.listar_itens_inicializacao()

    # ---------- Serviços ----------

    def listar_servicos(self) -> dict:
        return self._iniciar_job(
            lambda: {"ok": True, "servicos": servicos.listar_status_servicos()},
            operation_name="listar_servicos"
        )

    def desativar_servico(self, nome_servico: str) -> dict:
        """Desativa um serviço em segundo plano (fire-and-forget)."""
        def worker(job_context):
            self._require_protection()
            res = servicos.desativar_servico(nome_servico, cancel_event=job_context.cancel_event)
            if res.get("codigo") == "COMMAND_CANCELLED":
                from modules.core.exceptions import JobCancelledError
                raise JobCancelledError()
            return res
        return self._iniciar_job(
            worker,
            operation_name="desativar_servico",
            exclusive_group="system_mutation",
            pass_job_context=True
        )

    def restaurar_servico(self, nome_servico: str) -> dict:
        """Restaura um serviço gerenciado pelo Phoenix (fire-and-forget)."""
        def worker(job_context):
            self._require_protection()
            res = servicos.restaurar_servico(nome_servico, cancel_event=job_context.cancel_event)
            if res.get("codigo") == "COMMAND_CANCELLED":
                from modules.core.exceptions import JobCancelledError
                raise JobCancelledError()
            return res
        return self._iniciar_job(
            worker,
            operation_name="restaurar_servico",
            exclusive_group="system_mutation",
            pass_job_context=True
        )

    def iniciar_servico(self, nome_servico: str) -> dict:
        """Inicia um serviço que estava parado normalmente (fire-and-forget)."""
        def worker(job_context):
            self._require_protection()
            res = servicos.iniciar_servico(nome_servico, cancel_event=job_context.cancel_event)
            if res.get("codigo") == "COMMAND_CANCELLED":
                from modules.core.exceptions import JobCancelledError
                raise JobCancelledError()
            return res
        return self._iniciar_job(
            worker,
            operation_name="iniciar_servico",
            exclusive_group="system_mutation",
            pass_job_context=True
        )

    # ---------- Logs / relatório ----------

    def obter_historico(self) -> dict:
        try:
            atendimentos = logs.listar_atendimentos()
            return {"ok": True, "atendimentos": atendimentos}
        except Exception as e:
            return {"ok": False, "erro": str(e)}

    def executar_rotina_completa(self, nome_cliente: str = "") -> dict:
        """Executa a rotina completa em segundo plano (fire-and-forget)."""
        self.iniciar_atendimento(nome_cliente)

        def rotina(job_context=None):
            self._require_protection()
            return self._routine_service.executar(
                id_atendimento=self._id_atendimento,
                nome_cliente=self._nome_cliente,
                job_context=job_context
            )

        return self._iniciar_job(rotina, operation_name="rotina_completa", exclusive_group="system_mutation", pass_job_context=True)

    def liberar_memoria_standby(self) -> dict:
        return self._iniciar_job(
            lambda: {"ok": otimizacao.liberar_memoria_standby(),
                     "mensagem": "Memória standby liberada com sucesso"},
            operation_name="liberar_memoria",
            exclusive_group="system_mutation"
        )

    def analisar_startup(self) -> dict:
        return self._iniciar_job(
            lambda: {"ok": True,
                     "entradas": otimizacao.analisar_startup()},
            operation_name="analisar_startup"
        )

    # ---------- Arrastar Janela Frameless ----------

    def iniciar_drag(self, start_mouse_x: int, start_mouse_y: int, start_win_x: int, start_win_y: int):
        self._window_controller.iniciar_drag(start_mouse_x, start_mouse_y, start_win_x, start_win_y)

    def mover_janela(self, current_mouse_x: int, current_mouse_y: int):
        self._window_controller.mover_janela(current_mouse_x, current_mouse_y)

    def parar_drag(self):
        self._window_controller.parar_drag()

    # ---------- Janela ----------

    def minimizar_janela(self):
        self._window_controller.minimizar()

    def fechar_janela(self):
        self._window_controller.fechar()
        
    def shutdown(self):
        self._job_manager.shutdown()
        GUILogger.shutdown()
