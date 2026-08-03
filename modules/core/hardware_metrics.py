import logging
import psutil
import time
import threading
import math
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

def obter_uso_cpu(psutil_module=None) -> tuple:
    """
    Coleta o uso de CPU de forma bloqueante curta (0.1s) e calcula a média.
    Retorna uma tupla (uso_total, uso_por_nucleo).
    Retorna (None, None) em caso de falha ou indisponibilidade.
    """
    if psutil_module is None:
        import psutil
        psutil_module = psutil

    try:
        raw_cpu = psutil_module.cpu_percent(interval=0.1, percpu=True)
        if not raw_cpu:
            return None, None

        nucleos_validos = []
        for v in raw_cpu:
            try:
                f = float(v)
                if math.isfinite(f):
                    f = max(0.0, min(100.0, f))
                    nucleos_validos.append(f)
            except (ValueError, TypeError):
                continue

        if not nucleos_validos:
            return None, None

        media = sum(nucleos_validos) / len(nucleos_validos)
        media = round(media, 1)
        media = max(0.0, min(100.0, media))
        return media, nucleos_validos
    except Exception as e:
        logger.warning(f"Erro ao obter métricas de CPU: {e}")
        return None, None

def coletar_metricas_completas(psutil_module=None) -> dict:
    """Coleta uso de CPU, freqüência, memória, disco (stateful) e GPUs."""
    if psutil_module is None:
        import psutil
        psutil_module = psutil

    cpu_total, cpu_por_nucleo = obter_uso_cpu(psutil_module)

    try:
        freq = psutil_module.cpu_freq()
        freq_atual = round(freq.current, 0) if freq else None
    except Exception as e:
        logger.warning(f"Erro ao obter frequencia da CPU: {e}")
        freq_atual = None

    try:
        mem = psutil_module.virtual_memory()
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

    gpus_metrics = obter_metricas_gpu()

    return {
        "ok": True,
        "cpu": cpu_dict,
        "memoria": memoria_dict,
        "disco": disco_dict,
        "gpus": gpus_metrics
    }

def obter_metricas_gpu() -> list:
    """Extrai métricas das GPUs usando o módulo dedicado."""
    try:
        from modules.core.gpu_metrics import obter_metricas_gpu as gpu_collector
        return gpu_collector()
    except Exception as ex:
        logger.warning(f"Erro ao obter dados dinâmicos da GPU via módulo dedicado: {ex}")
        return []
