import logging
import threading

logger = logging.getLogger(__name__)

class WindowController:
    """
    Controlador dedicado para operações da janela frameless (webview).
    Encapsula o estado de drag (arrasto) e delega comandos para o objeto real da janela.
    """
    def __init__(self, window=None):
        self._window = window
        self._is_dragging = False
        self._drag_start_mouse_x = 0
        self._drag_start_mouse_y = 0
        self._drag_start_win_x = 0
        self._drag_start_win_y = 0
        self._lock = threading.RLock()

    def set_window(self, window):
        """Atribui o objeto da janela real ao controlador."""
        with self._lock:
            self._window = window

    def iniciar_drag(self, start_mouse_x, start_mouse_y, start_win_x, start_win_y):
        """Registra o estado inicial para começar a mover a janela."""
        try:
            with self._lock:
                self._drag_start_mouse_x = int(start_mouse_x)
                self._drag_start_mouse_y = int(start_mouse_y)
                self._drag_start_win_x = int(start_win_x)
                self._drag_start_win_y = int(start_win_y)
                self._is_dragging = True
        except Exception:
            logger.exception("Erro ao iniciar drag da janela")

    def mover_janela(self, current_mouse_x, current_mouse_y):
        """Calcula a nova posição com base no delta do mouse e move a janela."""
        try:
            with self._lock:
                if not self._is_dragging or not self._window:
                    return

                delta_x = int(current_mouse_x) - self._drag_start_mouse_x
                delta_y = int(current_mouse_y) - self._drag_start_mouse_y
                new_x = self._drag_start_win_x + delta_x
                new_y = self._drag_start_win_y + delta_y

                self._window.move(new_x, new_y)
        except Exception:
            logger.exception("Erro ao mover janela")

    def parar_drag(self):
        """Encerra o estado de arraste."""
        try:
            with self._lock:
                self._is_dragging = False
        except Exception:
            logger.exception("Erro ao parar drag da janela")

    def minimizar(self):
        """Minimiza a janela (delega para pywebview)."""
        try:
            with self._lock:
                if self._window:
                    self._window.minimize()
        except Exception:
            logger.exception("Erro ao minimizar janela")

    def fechar(self):
        """Fecha a janela (delega para pywebview)."""
        try:
            with self._lock:
                if self._window:
                    self._window.destroy()
        except Exception:
            logger.exception("Erro ao fechar janela")
