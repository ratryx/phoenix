import logging
import psutil
import time
import threading
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Stateful I/O tracking
_io_lock = threading.Lock()
_last_io_counters = None
_last_io_time = 0.0

def _get_disk_io_stateful() -> tuple[float, float]:
    """Retorna leitura e escrita em MB/s. Pode retornar None em caso de falha."""
    global _last_io_counters, _last_io_time

    try:
        current_counters = psutil.disk_io_counters()
    except Exception:
        return None, None

    current_time = time.monotonic()

    with _io_lock:
        if not current_counters:
            return None, None

        if _last_io_counters is None:
            _last_io_counters = current_counters
            _last_io_time = current_time
            return 0.0, 0.0 # First sample is warmup

        delta_time = current_time - _last_io_time
        if delta_time <= 0:
            return 0.0, 0.0

        # Handle possible counter resets (e.g. overflow, sleep/wake, disk reconnect)
        read_bytes = current_counters.read_bytes - _last_io_counters.read_bytes
        write_bytes = current_counters.write_bytes - _last_io_counters.write_bytes

        if read_bytes < 0 or write_bytes < 0:
            _last_io_counters = current_counters
            _last_io_time = current_time
            return 0.0, 0.0

        read_mb = round((read_bytes / (1024**2)) / delta_time, 1)
        write_mb = round((write_bytes / (1024**2)) / delta_time, 1)

        _last_io_counters = current_counters
        _last_io_time = current_time

        return read_mb, write_mb

def reset_io_counters():
    global _last_io_counters, _last_io_time
    with _io_lock:
        _last_io_counters = None
        _last_io_time = 0.0

def coletar_metricas_completas() -> dict:
    """Coleta uso de CPU, freqüência, memória, disco (stateful) e GPUs."""
    try:
        cpu_total = psutil.cpu_percent(interval=None)
        cpu_por_nucleo = psutil.cpu_percent(interval=None, percpu=True)
    except Exception as e:
        logger.warning(f"Erro ao obter métricas de CPU: {e}")
        cpu_total = None
        cpu_por_nucleo = []

    try:
        freq = psutil.cpu_freq()
        freq_atual = round(freq.current, 0) if freq else None
    except Exception as e:
        logger.warning(f"Erro ao obter frequencia da CPU: {e}")
        freq_atual = None

    try:
        mem = psutil.virtual_memory()
        memoria_dict = {
            "percentual_uso": round(mem.percent, 1),
            "usada_gb": round(mem.used / (1024**3), 1),
            "disponivel_gb": round(mem.available / (1024**3), 1)
        }
    except Exception as e:
        logger.warning(f"Erro ao obter métricas de memória: {e}")
        memoria_dict = {
            "percentual_uso": None,
            "usada_gb": None,
            "disponivel_gb": None
        }

    read_mb, write_mb = _get_disk_io_stateful()

    gpus_metrics = []
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        for g in gpus:
            gpus_metrics.append({
                "id": str(g.id),
                "nome": g.name,
                "uso_percentual": int(g.load * 100),
                "temperatura_c": int(g.temperature),
                "vram_usada_mb": int(g.memoryUsed),
                "vram_total_mb": int(g.memoryTotal)
            })
    except ImportError:
        pass
    except Exception as ex:
        logger.warning(f"Erro ao obter dados dinâmicos da GPU: {ex}")

    cpu_dict = {}
    if cpu_total is not None:
        cpu_dict["uso_percentual"] = cpu_total
    if cpu_por_nucleo:
        cpu_dict["uso_por_nucleo"] = cpu_por_nucleo
    if freq_atual is not None:
        cpu_dict["frequencia_atual_mhz"] = freq_atual

    disco_dict = {}
    if read_mb is not None:
        disco_dict["leitura_mb_s"] = read_mb
    if write_mb is not None:
        disco_dict["escrita_mb_s"] = write_mb

    return {
        "ok": True,
        "cpu": cpu_dict,
        "memoria": memoria_dict,
        "disco": disco_dict,
        "gpus": gpus_metrics
    }
