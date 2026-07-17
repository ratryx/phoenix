import uuid
from modules import diagnostico
from modules import limpeza
from modules import otimizacao
from modules import servicos
from modules import logs
from modules import relatorio
from modules.gui.jobs import JobManager


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
        self._job_manager = job_manager or JobManager()
        
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

    def _iniciar_job(self, target_fn, *args, operation_name="unknown", exclusive_group=None, **kwargs) -> dict:
        """Delega a criação do job para o JobManager e retorna o formato esperado pelo JS."""
        job_id = self._job_manager.submit(
            target_fn, 
            *args, 
            operation_name=operation_name, 
            exclusive_group=exclusive_group, 
            **kwargs
        )
        return {"job_id": job_id}

    def verificar_tarefa(self, job_id: str) -> dict:
        """Retorna o status atual de uma tarefa a partir do JobManager."""
        return self._job_manager.consultar(job_id)

    # ---------- Hardware / contexto inicial ----------

    def obter_hardware(self) -> dict:
        """Retorna o hardware já detectado pelo launcher (evita reconsultar)."""
        return self._hardware_service.obter_hardware()

    def obter_nivel_qualidade_visual(self) -> str:
        """
        Retorna 'alto', 'medio' ou 'baixo' para o front-end ajustar automaticamente
        a intensidade dos efeitos visuais (glassmorphism, partículas, blur).
        """
        return self._hardware_service.obter_nivel_qualidade_visual()

    # ---------- Atendimento ----------

    def iniciar_atendimento(self, nome_cliente: str = "") -> dict:
        self._nome_cliente = nome_cliente or ""
        self._id_atendimento = logs.gerar_id_atendimento()
        return {"id_atendimento": self._id_atendimento}

    def obter_clientes_portable(self) -> dict:
        """Lista clientes salvos no pen drive (modo portable)."""
        from modules.shared import IS_PORTABLE, listar_clientes_portable
        if not IS_PORTABLE:
            return {"ok": False, "portable": False}
        return {
            "ok": True,
            "portable": True,
            "clientes": listar_clientes_portable()
        }

    def selecionar_cliente(self, nome: str) -> dict:
        """Define o cliente ativo da sessão."""
        from modules.shared import (definir_cliente_ativo, 
                                    salvar_meta_cliente, IS_PORTABLE)
        if not nome or not nome.strip():
            return {"ok": False, "erro": "Nome inválido"}
        nome = nome.strip()
        definir_cliente_ativo(nome)
        if IS_PORTABLE:
            salvar_meta_cliente(nome)
        return {"ok": True, "cliente": nome}

    def remover_cliente_portable(self, id_cliente: str) -> dict:
        """Remove um cliente do pen drive."""
        from modules.shared import remover_cliente_portable
        if remover_cliente_portable(id_cliente):
            return {"ok": True}
        return {"ok": False, "erro": "Não foi possível remover o cliente"}

    def obter_modo_portable(self) -> dict:
        from modules.shared import IS_PORTABLE, CLIENTE_ATIVO
        return {
            "portable": IS_PORTABLE,
            "cliente_ativo": CLIENTE_ATIVO
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
        """Executa limpeza completa em segundo plano (fire-and-forget)."""
        return self._iniciar_job(
            lambda: {"ok": True, "espaco_liberado_mb": round(limpeza.executar_limpeza_completa(self._id_atendimento) / (1024 ** 2), 2)},
            operation_name="executar_limpeza",
            exclusive_group="system_mutation"
        )

    # ---------- Otimização ----------

    def criar_ponto_restauracao(self) -> dict:
        """Cria um ponto de restauração em segundo plano (fire-and-forget)."""
        return self._iniciar_job(
            otimizacao.criar_ponto_restauracao,
            operation_name="criar_ponto_restauracao",
            exclusive_group="system_mutation"
        )

    def carregar_hardware_cache(self) -> dict:
        """Carrega hardware do cache ou refaz scan (fire-and-forget)."""
        job_id = str(uuid.uuid4())

        def prog_cb(msg):
            pct = self._job_manager.get_progress(job_id)
            if "CPU" in msg: pct = 33
            elif "RAM" in msg: pct = 66
            elif "GPU" in msg: pct = 90
            elif "Final" in msg: pct = 100
            self._job_manager.update_progress(job_id, pct, msg)

        def worker():
            return self._hardware_service.carregar_hardware_cache(progress_callback=prog_cb)

        self._iniciar_job(worker, job_id=job_id, operation_name="carregar_hardware_cache")
        # Força status inicial de progresso pro front pegar a string imediata
        self._job_manager.update_progress(job_id, 0, "Iniciando detecção...")
        return {"job_id": job_id}

    def forcar_rescan_hardware(self) -> dict:
        """Força um scan completo de hardware (fire-and-forget)."""
        return self._iniciar_job(
            self._hardware_service.forcar_rescan_hardware,
            operation_name="forcar_rescan_hardware"
        )

    def executar_otimizacao_geral(self) -> dict:
        """Aplica otimizações gerais em segundo plano (fire-and-forget)."""
        def acao():
            otimizacao.executar_otimizacao_geral(self._id_atendimento)
            return {"ok": True}
        return self._iniciar_job(acao, operation_name="otimizacao_geral", exclusive_group="system_mutation")

    def executar_otimizacao_gaming(self, resetar_rede: bool = False) -> dict:
        """Aplica otimizações para jogos em segundo plano (fire-and-forget)."""
        def acao():
            otimizacao.ativar_plano_energia_alto_desempenho()
            otimizacao.ativar_modo_jogo_windows()
            otimizacao.desativar_gamebar_overlay()
            otimizacao.otimizar_gpu_para_jogos()
            if resetar_rede:
                otimizacao.limpar_dns_e_rede()
            if self._id_atendimento:
                logs.registrar_acao(self._id_atendimento, "Otimização para jogos aplicada")
            return {"ok": True}
        return self._iniciar_job(acao, operation_name="otimizacao_gaming", exclusive_group="system_mutation")

    def otimizar_disco(self) -> dict:
        """Otimiza o disco em segundo plano (fire-and-forget)."""
        return self._iniciar_job(
            lambda: {"ok": True, "saida": otimizacao.otimizar_disco_principal()},
            operation_name="otimizar_disco", 
            exclusive_group="system_mutation"
        )

    def listar_inicializacao(self) -> dict:
        try:
            saida = otimizacao.listar_itens_inicializacao()
            return {"ok": True, "saida": saida}
        except Exception as e:
            return {"ok": False, "erro": str(e)}

    # ---------- Serviços ----------

    def listar_servicos(self) -> dict:
        return self._iniciar_job(
            lambda: {"ok": True, "servicos": servicos.listar_status_servicos()},
            operation_name="listar_servicos"
        )

    def desativar_servico(self, nome_servico: str) -> dict:
        """Desativa um serviço em segundo plano (fire-and-forget)."""
        return self._iniciar_job(
            lambda: {"ok": servicos.desativar_servico(nome_servico)},
            operation_name="desativar_servico",
            exclusive_group="system_mutation"
        )

    def ativar_servico(self, nome_servico: str) -> dict:
        """Ativa um serviço em segundo plano (fire-and-forget)."""
        return self._iniciar_job(
            lambda: {"ok": servicos.ativar_servico(nome_servico)},
            operation_name="ativar_servico",
            exclusive_group="system_mutation"
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
        
        def rotina():
            return self._routine_service.executar(
                id_atendimento=self._id_atendimento,
                nome_cliente=self._nome_cliente
            )
            
        return self._iniciar_job(rotina, operation_name="rotina_completa", exclusive_group="system_mutation")

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
