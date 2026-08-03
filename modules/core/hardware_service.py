import logging
import threading
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
        self._rescan_lock = threading.Lock()
        self._rescan_promise = None

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
            self._hardware_metrics.reset_io_counters()
            self._boot_time = self._psutil.boot_time()
        except Exception:
            logger.exception("Falha ao preparar as métricas")

    def obter_hardware(self) -> dict:
        """Retorna o inventário estático."""
        return self._inventario

    def _inject_dynamic_capabilities(self, hw: dict):
        if not hw: return
        has_gputil = False
        try:
            import GPUtil
            has_gputil = len(GPUtil.getGPUs()) > 0
        except Exception:
            has_gputil = False

        if "capacidades" not in hw:
            hw["capacidades"] = {}

        hw["capacidades"]["metricas_gpu_disponiveis"] = has_gputil
        hw["capacidades"]["temperatura_gpu_disponivel"] = has_gputil
        hw["capacidades"]["vram_gpu_disponivel"] = has_gputil

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
                "cpu_percent": None,
                "ram_percent": None,
                "ram_disponivel_gb": None
            }

    def _format_uptime(self) -> str:
        if not self._boot_time:
            self._boot_time = self._psutil.boot_time()

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
        """Mescla o inventário estático com algumas métricas básicas para a página inicial."""
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
        if not gpus:
            return {"ok": True, "gpu": None}
        return {
            "ok": True,
            "gpu": gpus[0]
        }

    def carregar_hardware_cache(self, progress_callback=None) -> dict:
        hw = self._hardware_mod.obter_hardware_com_cache(progress_callback=progress_callback)
        self._inject_dynamic_capabilities(hw)
        self._inventario = hw
        return {"ok": True, "hardware": hw}

    def forcar_rescan_hardware(self, progress_callback=None) -> dict:
        is_leader = False
        with self._rescan_lock:
            if self._rescan_promise is None:
                self._rescan_promise = {"event": threading.Event(), "result": None}
                is_leader = True
            promise = self._rescan_promise

        if is_leader:
            try:
                hw = self._hardware_mod.coletar_hardware_completo(progress_callback=progress_callback)
                self._inject_dynamic_capabilities(hw)
                self._inventario = hw
                promise["result"] = {"ok": True, "hardware": hw}
            except Exception as e:
                logger.exception("Falha no rescan_hardware")
                promise["result"] = {
                    "ok": False,
                    "codigo": "HARDWARE_RESCAN_FAILED",
                    "erro": "Não foi possível atualizar o inventário de hardware."
                }
            finally:
                promise["event"].set()
                with self._rescan_lock:
                    if self._rescan_promise is promise:
                        self._rescan_promise = None
        else:
            promise["event"].wait()

        return promise["result"]
