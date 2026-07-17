"""
Phoenix Optimizer — Modo GUI (backend)

Cria a janela da interface gráfica usando pywebview (HTML/CSS/JS renderizado
via WebView2 no Windows — não embute um navegador completo, usa o motor já
presente no sistema, mantendo o programa leve).

A classe PhoenixAPI expõe métodos Python que o JavaScript do front-end chama
diretamente (via `pywebview.api.<metodo>`), e cada método aqui apenas delega
para o núcleo compartilhado em modules/ — a mesma lógica usada pelo modo CLI.
Isso garante que CLI e GUI nunca fiquem com comportamentos diferentes.
"""

import os
import sys
import uuid
import threading
import webview

from modules import diagnostico
from modules import limpeza
from modules import otimizacao
from modules import servicos
from modules import logs
from modules import relatorio
from modules import hardware as hardware_mod
from modules.gui.jobs import JobManager


class PhoenixAPI:
    """
    Ponte entre o front-end (HTML/JS) e o núcleo de funcionalidades do Phoenix.
    Cada método retorna dados em formas simples (dict/list/str) que o
    pywebview serializa automaticamente para JSON no lado do JavaScript.
    """

    def __init__(self, hw_info: dict, job_manager=None):
        self._hw_info = hw_info
        self._id_atendimento = None
        self._nome_cliente = ""
        self._janela = None
        self._job_manager = job_manager or JobManager()

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
        return self._hw_info

    def obter_nivel_qualidade_visual(self) -> str:
        """
        Retorna 'alto', 'medio' ou 'baixo' para o front-end ajustar automaticamente
        a intensidade dos efeitos visuais (glassmorphism, partículas, blur).
        """
        return hardware_mod.classificar_capacidade_hardware(self._hw_info)

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
        """Retorna CPU% e RAM% instantâneos sem bloquear (interval=0). Uso: polling de tempo real na GUI."""
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)  # bloqueia 100ms mas retorna valor real
        mem = psutil.virtual_memory()
        freq = psutil.cpu_freq()
        return {
            "ok": True,
            "cpu_percent": cpu,
            "ram_percent": round(mem.percent, 1),
            "ram_disponivel_gb": round(mem.available / (1024**3), 1),
            "cpu_freq_mhz": round(freq.current, 0) if freq else None
        }
    def obter_info_sistema_detalhado(self) -> dict:
        import platform, psutil
        
        # CPU
        freq = psutil.cpu_freq()
        
        # Disco por partição
        discos = []
        for p in psutil.disk_partitions():
            try:
                uso = psutil.disk_usage(p.mountpoint)
                discos.append({
                    "unidade": p.device,
                    "fstype": p.fstype,
                    "total_gb": round(uso.total / (1024**3), 1),
                    "usado_gb": round(uso.used / (1024**3), 1),
                    "livre_gb": round(uso.free / (1024**3), 1),
                    "percentual": uso.percent
                })
            except Exception:
                continue
        
        # RAM detalhada
        mem = psutil.virtual_memory()
        try:
            swap = psutil.swap_memory()
            swap_total = round(swap.total / (1024**3), 1)
            swap_usado = round(swap.used / (1024**3), 1)
        except Exception:
            swap_total = None
            swap_usado = None
        
        # Sistema
        boot_time = psutil.boot_time()
        from datetime import datetime
        uptime_segundos = (datetime.now() - datetime.fromtimestamp(boot_time)).seconds
        horas = uptime_segundos // 3600
        minutos = (uptime_segundos % 3600) // 60
        
        return {
            "ok": True,
            "sistema": {
                "os": f"{platform.system()} {platform.release()}",
                "versao": platform.version()[:50],
                "arquitetura": platform.machine(),
                "uptime": f"{horas}h {minutos}m"
            },
            "cpu": {
                "modelo": self._hw_info.get("cpu", {}).get("modelo", "N/A"),
                "nucleos_fisicos": psutil.cpu_count(logical=False),
                "nucleos_logicos": psutil.cpu_count(logical=True),
                "freq_atual": round(freq.current, 0) if freq else None,
                "freq_max": round(freq.max, 0) if freq and freq.max else None,
                "freq_min": round(freq.min, 0) if freq and freq.min else None,
                "arquitetura": platform.machine()
            },
            "ram": {
                "total_gb": round(mem.total / (1024**3), 1),
                "disponivel_gb": round(mem.available / (1024**3), 1),
                "usada_gb": round(mem.used / (1024**3), 1),
                "percentual": round(mem.percent, 1),
                "swap_total_gb": swap_total,
                "swap_usado_gb": swap_usado
            },
            "discos": discos,
            "gpus": self._hw_info.get("gpus", [])
        }

    def obter_metricas_completas(self) -> dict:
        import psutil, time
        
        # CPU
        cpu_total = psutil.cpu_percent(interval=0.1)
        cpu_por_nucleo = psutil.cpu_percent(interval=None, percpu=True)
        freq = psutil.cpu_freq()
        
        # RAM
        mem = psutil.virtual_memory()
        
        # Disco I/O (delta)
        io1 = psutil.disk_io_counters()
        time.sleep(0.5)
        io2 = psutil.disk_io_counters()
        read_mb = round((io2.read_bytes - io1.read_bytes) / (1024**2) / 0.5, 1) if io1 and io2 else 0
        write_mb = round((io2.write_bytes - io1.write_bytes) / (1024**2) / 0.5, 1) if io1 and io2 else 0
        
        # GPU
        gpu_data = None
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                g = gpus[0]
                gpu_data = {
                    "nome": g.name,
                    "uso": int(g.load * 100),
                    "temp": int(g.temperature),
                    "vram_usada": int(g.memoryUsed),
                    "vram_total": int(g.memoryTotal)
                }
        except Exception:
            pass
        
        return {
            "ok": True,
            "cpu": {
                "total": cpu_total,
                "por_nucleo": cpu_por_nucleo,
                "freq_mhz": round(freq.current, 0) if freq else None,
                "nucleos": len(cpu_por_nucleo)
            },
            "ram": {
                "percent": round(mem.percent, 1),
                "usada_gb": round(mem.used / (1024**3), 1),
                "total_gb": round(mem.total / (1024**3), 1),
                "disponivel_gb": round(mem.available / (1024**3), 1)
            },
            "disco": {
                "leitura_mb": read_mb,
                "escrita_mb": write_mb
            },
            "gpu": gpu_data
        }

    def obter_gpu_rapida(self) -> dict:
        """Retorna métricas rápidas da GPU primária via GPUtil (uso, temp, VRAM)."""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                g = gpus[0]
                return {
                    "ok": True,
                    "gpu": {
                        "uso": int(g.load * 100),
                        "temp": int(g.temperature),
                        "vram_usada": int(g.memoryUsed),
                        "vram_total": int(g.memoryTotal)
                    }
                }
        except Exception:
            pass
        return {"ok": False, "gpu": None}

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
        # Inicializa o job com mensagem customizada antes de rodar a thread (para o JS exibir "Iniciando detecção...")
        # Isso é gerenciado pelo JobManager agora. Submetemos e depois o callback atualiza.

        def prog_cb(msg):
            pct = self._job_manager.get_progress(job_id)
            if "CPU" in msg: pct = 33
            elif "RAM" in msg: pct = 66
            elif "GPU" in msg: pct = 90
            elif "Final" in msg: pct = 100
            self._job_manager.update_progress(job_id, pct, msg)

        def worker():
            hw = hardware_mod.obter_hardware_com_cache(progress_callback=prog_cb)
            self._hw_info = hw
            return {"ok": True, "hardware": hw}

        self._iniciar_job(worker, job_id=job_id, operation_name="carregar_hardware_cache")
        # Força status inicial de progresso pro front pegar a string imediata
        self._job_manager.update_progress(job_id, 0, "Iniciando detecção...")
        return {"job_id": job_id}

    def forcar_rescan_hardware(self) -> dict:
        """Força um scan completo de hardware (fire-and-forget)."""
        return self._iniciar_job(
            lambda: {"ok": True, "hardware": hardware_mod.coletar_hardware_completo()},
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
        def rotina():
            self.iniciar_atendimento(nome_cliente)
            id_atendimento = self._id_atendimento

            dados_antes = diagnostico.coletar_diagnostico_silencioso()
            logs.salvar_snapshot(id_atendimento, "antes", dados_antes, self._nome_cliente)
            logs.registrar_acao(id_atendimento, "Diagnóstico inicial coletado", nome_cliente=self._nome_cliente)

            espaco_liberado = limpeza.executar_limpeza_completa(id_atendimento)
            otimizacao.executar_otimizacao_geral(id_atendimento)

            dados_depois = diagnostico.coletar_diagnostico_silencioso()
            logs.salvar_snapshot(id_atendimento, "depois", dados_depois, self._nome_cliente)
            logs.registrar_acao(id_atendimento, "Diagnóstico final coletado")

            espaco_liberado_mb = round(espaco_liberado / (1024 ** 2), 2)

            pasta_logs = logs.obter_pasta_logs()
            caminho_txt = pasta_logs / f"{id_atendimento}_relatorio.txt"
            snapshot_antes = logs.carregar_snapshot(id_atendimento, "antes")
            snapshot_depois = logs.carregar_snapshot(id_atendimento, "depois")
            relatorio.exportar_relatorio_txt(snapshot_antes, snapshot_depois, espaco_liberado_mb, caminho_txt)

            return {
                "ok": True,
                "id_atendimento": id_atendimento,
                "antes": dados_antes,
                "depois": dados_depois,
                "espaco_liberado_mb": espaco_liberado_mb,
                "relatorio_txt": str(caminho_txt),
            }
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
        self._drag_start_mouse_x = start_mouse_x
        self._drag_start_mouse_y = start_mouse_y
        self._drag_start_win_x = start_win_x
        self._drag_start_win_y = start_win_y
        self._is_dragging = True

    def mover_janela(self, current_mouse_x: int, current_mouse_y: int):
        if hasattr(self, "_is_dragging") and self._is_dragging and self._janela:
            delta_x = current_mouse_x - self._drag_start_mouse_x
            delta_y = current_mouse_y - self._drag_start_mouse_y
            new_x = self._drag_start_win_x + delta_x
            new_y = self._drag_start_win_y + delta_y
            self._janela.move(new_x, new_y)

    def parar_drag(self):
        self._is_dragging = False

    # ---------- Janela ----------

    def minimizar_janela(self):
        for janela in webview.windows:
            janela.minimize()

    def fechar_janela(self):
        for janela in webview.windows:
            janela.destroy()


def _caminho_recurso(caminho_relativo: str) -> str:
    """
    Resolve caminhos de arquivos da GUI tanto em modo desenvolvimento
    quanto quando empacotado pelo PyInstaller (onde os arquivos ficam
    em uma pasta temporária referenciada por sys._MEIPASS).
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, caminho_relativo)


def iniciar(hw_info: dict = None):
    """Ponto de entrada do modo GUI, chamado pelo launcher.py."""
    if hw_info is None:
        hw_info = {
            "sistema_operacional": "",
            "cpu": {"modelo": "", "nucleos_fisicos": 0, "nucleos_logicos": 0, 
                    "frequencia_atual_mhz": None, "frequencia_max_mhz": None, 
                    "uso_percentual": 0},
            "ram": {"total_gb": 0, "disponivel_gb": 0, "percentual_uso": 0},
            "gpus": []
        }

    api = PhoenixAPI(hw_info)
    caminho_html = _caminho_recurso(os.path.join("gui", "index.html"))

    janela = webview.create_window(
        title="Phoenix Optimizer",
        url=caminho_html,
        js_api=api,
        width=1100,
        height=720,
        min_size=(900, 600),
        frameless=True,
        easy_drag=False,
        background_color="#15120F",
    )

    api._janela = janela

    import psutil as _psutil
    _psutil.cpu_percent(interval=None)  # chamada de aquecimento

    webview.start(debug=False)


if __name__ == "__main__":
    iniciar()
