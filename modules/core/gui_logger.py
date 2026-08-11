import logging
import logging.handlers
import queue
import ctypes
import sys
import threading
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_QUICK_EDIT_MODE = 0x0040

def disable_quickedit():
    if sys.platform != "win32": return
    try:
        kernel32 = ctypes.windll.kernel32
        h_stdout = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE = -10
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
            mode.value &= ~ENABLE_QUICK_EDIT_MODE
            mode.value |= ENABLE_EXTENDED_FLAGS
            kernel32.SetConsoleMode(h_stdout, mode)
    except Exception:
        pass

class RichTerminalHandler(logging.Handler):
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
    _lock = threading.Lock()
    _progress = None
    _tasks = {}

    def __init__(self):
        self.log_queue = queue.Queue(-1)
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

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        self.logger.addHandler(queue_handler)
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
        with cls._lock:
            if cls._progress is not None:
                cls._progress.stop()
                cls._progress = None
            cls._tasks.clear()

    @classmethod
    def log(cls, operation, status, message=""):
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

    @classmethod
    def log_job_progress(cls, job_id, pct, msg, details=None):
        with cls._lock:
            if cls._progress is None:
                from modules.shared import console as shared_console
                cls._progress = Progress(
                    TextColumn("[cyan]{task.description}"),
                    BarColumn(bar_width=40),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=shared_console,
                    transient=True
                )
                cls._progress.start()

            if job_id not in cls._tasks:
                cls._tasks[job_id] = cls._progress.add_task(msg, total=100)

            cls._progress.update(cls._tasks[job_id], completed=pct, description=msg)

    @classmethod
    def log_job_terminal_state(cls, job_id, job):
        with cls._lock:
            if job_id in cls._tasks and cls._progress:
                cls._progress.remove_task(cls._tasks[job_id])
                del cls._tasks[job_id]

                if not cls._tasks:
                    cls._progress.stop()
                    cls._progress = None

        status = job.get("status")
        res = job.get("resultado") or {}
        op_raw = job.get("operation_name", "unknown")

        friendly_names = {
            "executar_limpeza": "Limpeza do sistema",
            "criar_ponto_restauracao": "Ponto de restauração",
            "rotina_completa": "Rotina completa",
            "iniciar_atualizacao": "Atualização de hardware",
            "forcar_rescan_hardware": "Rescan de hardware",
            "otimizar_disco": "Otimização de disco",
            "otimizacao_geral": "Otimização geral",
            "otimizacao_gaming": "Otimização para jogos"
        }
        op = friendly_names.get(op_raw, op_raw)

        if status == "done":
            if op_raw == "criar_ponto_restauracao":
                if res.get("ok"):
                    cls.log(op, "OK", "Ponto de restauração criado e verificado.")
                else:
                    erro = res.get("erro", "Não foi possível criar um ponto de restauração.")
                    cls.log(op, "AVISO", f"{erro}")
            else:
                parcial = res.get("parcial", False)
                if parcial:
                    cls.log(op, "AVISO", f"Operação '{op}' concluída com avisos.")
                else:
                    cls.log(op, "OK", f"Operação '{op}' concluída com sucesso.")
        elif status == "failed":
            codigo = res.get("codigo", "ERRO_DESCONHECIDO")
            if codigo == "JOB_CONFLICT":
                cls.log(op, "ERRO", f"Operação '{op}' ignorada (conflito).")
            else:
                cls.log(op, "ERRO", f"Operação '{op}' falhou: {codigo}")
        elif status == "cancelled":
            cls.log(op, "ERRO", f"Operação '{op}' cancelada pelo usuário (JOB_CANCELLED).")
        elif status == "timed_out":
            cls.log(op, "ERRO", f"Operação '{op}' excedeu o tempo limite (JOB_TIMEOUT).")
