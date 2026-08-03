import csv
import io
import math
import logging
from modules.core.windows_command import run_windows_command

logger = logging.getLogger(__name__)

def _parse_numeric(val_str, min_val=0, max_val=None, allow_zero=True):
    val_str = val_str.strip() if val_str else ""
    if not val_str or val_str.upper() in ("N/A", "[N/A]", "NOT SUPPORTED", "NAN", "INF", "+INF", "-INF", "INFINITY"):
        return None
        
    try:
        val = float(val_str)
    except ValueError:
        return None
        
    if not math.isfinite(val):
        return None
        
    if not allow_zero and val == 0:
        return None
        
    if val < min_val:
        return None
        
    if max_val is not None and val > max_val:
        return None
        
    return int(val)

def obter_metricas_gpu() -> list:
    """Extrai métricas das GPUs usando nvidia-smi de forma silenciosa e controlada."""
    gpus_metrics = []
    
    try:
        # Chama nvidia-smi pedindo campos específicos formatados como CSV
        # index, name, utilization.gpu, temperature.gpu, memory.used, memory.total
        cmd = [
            "nvidia-smi",
            "--query-gpu=index,name,utilization.gpu,temperature.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits"
        ]
        
        result = run_windows_command(
            cmd,
            operation_name="Obter metricas GPU",
            timeout_seconds=2.0
        )

        if not result.ok or not result.stdout.strip():
            return []

        reader = csv.reader(io.StringIO(result.stdout.strip()))
        for partes in reader:
            if len(partes) < 6:
                continue
                
            try:
                gpu_id = partes[0].strip()
                nome = partes[1].strip()
                
                # Valores numéricos
                uso = _parse_numeric(partes[2], min_val=0, max_val=100, allow_zero=True)
                temp = _parse_numeric(partes[3], min_val=0, max_val=None, allow_zero=True)
                vram_usada = _parse_numeric(partes[4], min_val=0, max_val=None, allow_zero=True)
                vram_total = _parse_numeric(partes[5], min_val=0.0001, max_val=None, allow_zero=False)
                
                gpus_metrics.append({
                    "id": gpu_id,
                    "nome": nome,
                    "uso_percentual": uso,
                    "temperatura_c": temp,
                    "vram_usada_mb": vram_usada,
                    "vram_total_mb": vram_total
                })
            except Exception as e:
                logger.debug(f"Erro ao parsear linha nvidia-smi: {e}")
                
    except Exception as ex:
        logger.warning(f"Erro inesperado ao obter dados dinâmicos da GPU: {ex}")
        
    return gpus_metrics
