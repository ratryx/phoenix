import logging
import logging.handlers
import queue
import ctypes
import sys
from rich.console import Console

ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_QUICK_EDIT_MODE = 0x0040

def disable_quickedit():
    """Desabilita QuickEdit mode para evitar que cliques no console congelem o executável."""
    if sys.platform != "win32":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        h_stdout = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE = -10
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
            mode.value &= ~ENABLE_QUICK_EDIT_MODE
            # O ENABLE_EXTENDED_FLAGS deve ser setado de volta junto ou o quick edit mode não altera
            mode.value |= ENABLE_EXTENDED_FLAGS
            kernel32.SetConsoleMode(h_stdout, mode)
    except Exception:
        pass

class RichTerminalHandler(logging.Handler):
    """Handler simples que escreve no console via Rich sem formatadores do python."""
    def __init__(self, rich_console):
        super().__init__()
        self.rich_console = rich_console

    def emit(self, record):
        try:
            msg = self.format(record)
            self.rich_console.print(msg)
        except Exception:
            self.handleError(record)

class GUILogger:
    _instance = None
    
    def __init__(self):
        self.log_queue = queue.Queue(-1)
        
        # O console do rich compartilhado
        from modules.shared import console as shared_console
        
        rich_handler = RichTerminalHandler(shared_console)
        rich_handler.setFormatter(logging.Formatter("%(message)s"))
        
        self.queue_listener = logging.handlers.QueueListener(
            self.log_queue, 
            rich_handler, 
            respect_handler_level=True
        )
        
        self.logger = logging.getLogger("gui_terminal_logger")
        self.logger.setLevel(logging.INFO)
        
        # Limpa handlers anteriores para evitar repetição
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        self.logger.addHandler(queue_handler)
        
        # Não propaga pro root logger
        self.logger.propagate = False

    @classmethod
    def setup(cls):
        if cls._instance is None:
            disable_quickedit()
            cls._instance = cls()
            cls._instance.queue_listener.start()
            
    @classmethod
    def shutdown(cls):
        if cls._instance is not None:
            cls._instance.queue_listener.stop()
            cls._instance = None

    @classmethod
    def log(cls, operation, status, message=""):
        """
        operation: Ex: "Limpeza do sistema"
        status: "INICIO", "OK", "AVISO", "ERRO"
        message: Ex: "Limpeza concluída sem erros..."
        """
        if cls._instance:
            color = {
                "INICIO": "cyan",
                "OK": "green",
                "AVISO": "yellow",
                "ERRO": "red"
            }.get(status, "white")
            
            if status == "INICIO":
                formatted = f"[dim]\\[GUI][/dim] [[{color}]{status}[/{color}]] {operation}"
            else:
                formatted = f"[dim]\\[GUI][/dim] [[{color}]{status}[/{color}]] {message}"
                
            cls._instance.logger.info(formatted)
