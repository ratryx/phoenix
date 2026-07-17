"""
Phoenix Optimizer — Modo GUI (backend)

Cria a janela da interface gráfica usando pywebview (HTML/CSS/JS renderizado
via WebView2 no Windows — não embute um navegador completo, usa o motor já
presente no sistema, mantendo o programa leve).
"""

import os
import sys
import webview

# Re-export temporário para manter compatibilidade
from modules.gui.api import PhoenixAPI


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

    from modules.core.hardware_service import HardwareService
    from modules.gui.window_controller import WindowController
    
    hardware_service = HardwareService(hw_info=hw_info)
    hardware_service.preparar_metricas()

    window_controller = WindowController()

    api = PhoenixAPI(hw_info, hardware_service=hardware_service, window_controller=window_controller)
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

    window_controller.set_window(janela)

    webview.start(debug=False)


if __name__ == "__main__":
    iniciar()
