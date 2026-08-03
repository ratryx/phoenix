import logging
from modules.core.windows_command import run_windows_command

logger = logging.getLogger(__name__)

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

        for line in result.stdout.strip().split("\n"):
            partes = [p.strip() for p in line.split(",")]
            if len(partes) < 6:
                continue
                
            try:
                gpu_id = partes[0]
                nome = partes[1]
                
                # Valores numéricos
                uso = int(partes[2]) if partes[2].isdigit() else 0
                temp = int(partes[3]) if partes[3].isdigit() else 0
                vram_usada = int(partes[4]) if partes[4].isdigit() else 0
                vram_total = int(partes[5]) if partes[5].isdigit() else 0
                
                gpus_metrics.append({
                    "id": gpu_id,
                    "nome": nome,
                    "uso_percentual": uso,
                    "temperatura_c": temp,
                    "vram_usada_mb": vram_usada,
                    "vram_total_mb": vram_total
                })
            except Exception as e:
                logger.debug(f"Erro ao parsear linha nvidia-smi '{line}': {e}")
                
    except Exception as ex:
        logger.warning(f"Erro inesperado ao obter dados dinâmicos da GPU: {ex}")
        
    return gpus_metrics
