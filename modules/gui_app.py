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

# Dicionário global para controle de tarefas em segundo plano (fire-and-forget)
# job_id -> {"status": "running" | "done", "resultado": ...}
_tarefas = {}


class PhoenixAPI:
    """
    Ponte entre o front-end (HTML/JS) e o núcleo de funcionalidades do Phoenix.
    Cada método retorna dados em formas simples (dict/list/str) que o
    pywebview serializa automaticamente para JSON no lado do JavaScript.
    """

    def __init__(self, hw_info: dict):
        self._hw_info = hw_info
        self._id_atendimento = None
        self._nome_cliente = ""
        self.janela = None

    def _iniciar_job(self, target_fn, *args, **kwargs) -> dict:
        """Inicia um job em segundo plano, retornando o job_id imediatamente."""
        job_id = str(uuid.uuid4())
        _tarefas[job_id] = {"status": "running", "resultado": None}

        def worker():
            try:
                res = target_fn(*args, **kwargs)
            except Exception as e:
                import traceback
                res = {"ok": False, "erro": str(e), "detalhe": traceback.format_exc()}
            _tarefas[job_id] = {"status": "done", "resultado": res}

        threading.Thread(target=worker, daemon=True).start()
        return {"job_id": job_id}

    def verificar_tarefa(self, job_id: str) -> dict:
        """Retorna o status atual de uma tarefa."""
        return _tarefas.get(job_id, {"status": "not_found"})

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

    # ---------- Diagnóstico ----------

    def obter_diagnostico(self) -> dict:
        """Coleta diagnóstico completo em segundo plano para exibir na GUI (fire-and-forget)."""
        return self._iniciar_job(lambda: {"ok": True, "dados": diagnostico.coletar_diagnostico_silencioso()})

    # ---------- Limpeza ----------

    def executar_limpeza(self) -> dict:
        """Executa limpeza completa em segundo plano (fire-and-forget)."""
        return self._iniciar_job(
            lambda: {"ok": True, "espaco_liberado_mb": round(limpeza.executar_limpeza_completa(self._id_atendimento) / (1024 ** 2), 2)}
        )

    # ---------- Otimização ----------

    def criar_ponto_restauracao(self) -> dict:
        """Cria um ponto de restauração em segundo plano (fire-and-forget)."""
        return self._iniciar_job(otimizacao.criar_ponto_restauracao)

    def executar_otimizacao_geral(self) -> dict:
        """Aplica otimizações gerais em segundo plano (fire-and-forget)."""
        def acao():
            otimizacao.executar_otimizacao_geral(self._id_atendimento)
            return {"ok": True}
        return self._iniciar_job(acao)

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
        return self._iniciar_job(acao)

    def otimizar_disco(self) -> dict:
        """Otimiza o disco em segundo plano (fire-and-forget)."""
        return self._iniciar_job(lambda: {"ok": True, "saida": otimizacao.otimizar_disco_principal()})

    def listar_inicializacao(self) -> dict:
        try:
            saida = otimizacao.listar_itens_inicializacao()
            return {"ok": True, "saida": saida}
        except Exception as e:
            return {"ok": False, "erro": str(e)}

    # ---------- Serviços ----------

    def listar_servicos(self) -> dict:
        try:
            return {"ok": True, "servicos": servicos.listar_status_servicos()}
        except Exception as e:
            return {"ok": False, "erro": str(e)}

    def desativar_servico(self, nome_servico: str) -> dict:
        """Desativa um serviço em segundo plano (fire-and-forget)."""
        return self._iniciar_job(lambda: {"ok": servicos.desativar_servico(nome_servico)})

    def ativar_servico(self, nome_servico: str) -> dict:
        """Ativa um serviço em segundo plano (fire-and-forget)."""
        return self._iniciar_job(lambda: {"ok": servicos.ativar_servico(nome_servico)})

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
        return self._iniciar_job(rotina)

    # ---------- Arrastar Janela Frameless ----------

    def iniciar_drag(self, start_mouse_x: int, start_mouse_y: int, start_win_x: int, start_win_y: int):
        self._drag_start_mouse_x = start_mouse_x
        self._drag_start_mouse_y = start_mouse_y
        self._drag_start_win_x = start_win_x
        self._drag_start_win_y = start_win_y
        self._is_dragging = True

    def mover_janela(self, current_mouse_x: int, current_mouse_y: int):
        if hasattr(self, "_is_dragging") and self._is_dragging and self.janela:
            delta_x = current_mouse_x - self._drag_start_mouse_x
            delta_y = current_mouse_y - self._drag_start_mouse_y
            new_x = self._drag_start_win_x + delta_x
            new_y = self._drag_start_win_y + delta_y
            self.janela.move(new_x, new_y)

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
        hw_info = hardware_mod.coletar_hardware_completo()

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

    api.janela = janela

    webview.start(debug=False)


if __name__ == "__main__":
    iniciar()
