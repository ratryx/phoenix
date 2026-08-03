import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HardwareService:
    """
    Serviço dedicado a gerenciar o estado estático e buscar métricas dinâmicas de hardware.
    Separando de forma clara inventário de métricas ao vivo.
    """
    def __init__(
        self,
        hw_info: Optional[Dict[str, Any]] = None,
        psutil_module=None,
        hardware_mod=None,
        hardware_metrics_mod=None
    ):
        self._inventario = hw_info or {}
        self._boot_time = None
        
        # Injeção de dependências
        if psutil_module is None:
            import psutil
            psutil_module = psutil
        if hardware_mod is None:
            from modules import hardware as hw
            hardware_mod = hw
        if hardware_metrics_mod is None:
            from modules.core import hardware_metrics
            hardware_metrics_mod = hardware_metrics
            
        self._psutil = psutil_module
        self._hardware_mod = hardware_mod
        self._hardware_metrics = hardware_metrics_mod

    def preparar_metricas(self) -> None:
        """Faz o aquecimento das métricas (ex: I/O stateful e CPU warmup)."""
        try:
            self._psutil.cpu_percent(interval=None)
            self._hardware_metrics._get_disk_io_stateful()
            self._boot_time = self._psutil.boot_time()
        except Exception:
            logger.exception("Falha ao preparar as métricas")

    def obter_hardware(self) -> dict:
        """Retorna o inventário estático."""
        return self._inventario

    def obter_nivel_qualidade_visual(self) -> str:
        return self._hardware_mod.classificar_capacidade_hardware(self._inventario)

    def obter_metricas_rapidas(self) -> dict:
        """Métricas curtas para CPU e RAM."""
        try:
            cpu = self._psutil.cpu_percent(interval=None)
            mem = self._psutil.virtual_memory()
            return {
                "ok": True,
                "cpu_percent": cpu,
                "ram_percent": round(mem.percent, 1),
                "ram_disponivel_gb": round(mem.available / (1024**3), 1),
            }
        except Exception:
            logger.exception("Falha ao obter_metricas_rapidas")
            return {
                "ok": False,
                "cpu_percent": 0.0,
                "ram_percent": 0.0,
                "ram_disponivel_gb": 0.0
            }

    def _format_uptime(self) -> str:
        if not self._boot_time:
            self._boot_time = self._psutil.boot_time()
        
        # total_seconds is a float, timedelta.seconds only gives the seconds remainder after days
        uptime_total_sec = (datetime.now() - datetime.fromtimestamp(self._boot_time)).total_seconds()
        
        if uptime_total_sec < 0:
            uptime_total_sec = 0
            
        dias = int(uptime_total_sec // 86400)
        horas = int((uptime_total_sec % 86400) // 3600)
        minutos = int((uptime_total_sec % 3600) // 60)
        
        if dias > 0:
            return f"{dias}d {horas}h {minutos}m"
        elif horas > 0:
            return f"{horas}h {minutos}m"
        else:
            return f"{minutos}m"

    def obter_info_sistema_detalhado(self) -> dict:
        """Mescla o inventário estático com algumas métricas básicas para a página inicial (se necessário), ou apenas os dados formatados."""
        # Delega ao métricas completas para a nova versão
        return self.obter_metricas_completas()

    def obter_metricas_completas(self) -> dict:
        """Obtém as métricas dinâmicas de todos os componentes (CPU, RAM, Disco, GPU)."""
        metrics = self._hardware_metrics.coletar_metricas_completas()
        metrics["uptime"] = self._format_uptime()
        return metrics

    def obter_gpu_rapida(self) -> dict:
        """Obtém métricas dinâmicas apenas da GPU principal."""
        metrics = self._hardware_metrics.coletar_metricas_completas()
        gpus = metrics.get("gpus", [])
        return {
            "ok": True,
            "gpu": gpus[0] if gpus else None
        }

    def carregar_hardware_cache(self, progress_callback=None) -> dict:
        hw = self._hardware_mod.obter_hardware_com_cache(progress_callback=progress_callback)
        self._inventario = hw
        return {"ok": True, "hardware": hw}

    def forcar_rescan_hardware(self, progress_callback=None) -> dict:
        hw = self._hardware_mod.coletar_hardware_completo(progress_callback=progress_callback)
        self._inventario = hw
        return {"ok": True, "hardware": hw}
