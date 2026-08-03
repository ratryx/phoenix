import logging
import psutil
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Stateful I/O tracking
_last_io_counters = None
_last_io_time = 0.0

def _get_disk_io_stateful() -> tuple[float, float]:
    global _last_io_counters, _last_io_time
    
    current_counters = psutil.disk_io_counters()
    current_time = time.monotonic()
    
    if not current_counters:
        return 0.0, 0.0
        
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
    global _last_io_counters
    _last_io_counters = None

def coletar_metricas_completas() -> dict:
    """Coleta uso de CPU, freqüência, memória, disco (stateful) e GPUs."""
    cpu_total = psutil.cpu_percent(interval=None) # Assume warmup elsewhere or use 0 on first call
    cpu_por_nucleo = psutil.cpu_percent(interval=None, percpu=True)
    
    try:
        freq = psutil.cpu_freq()
        freq_atual = round(freq.current, 0) if freq else None
    except Exception:
        freq_atual = None
        
    mem = psutil.virtual_memory()
    read_mb, write_mb = _get_disk_io_stateful()
    
    gpus_metrics = []
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        for g in gpus:
            gpus_metrics.append({
                "id": str(g.id), # Try to map with inventory if possible, but just rely on index/name for now
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

    return {
        "ok": True,
        "cpu": {
            "uso_percentual": cpu_total,
            "uso_por_nucleo": cpu_por_nucleo,
            "frequencia_atual_mhz": freq_atual
        },
        "memoria": {
            "percentual_uso": round(mem.percent, 1),
            "usada_gb": round(mem.used / (1024**3), 1),
            "disponivel_gb": round(mem.available / (1024**3), 1)
        },
        "disco": {
            "leitura_mb_s": read_mb,
            "escrita_mb_s": write_mb
        },
        "gpus": gpus_metrics
    }
