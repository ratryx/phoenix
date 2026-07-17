import logging
import uuid
import time
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class HardwareService:
    """
    Serviço dedicado à coleta e formatação de métricas de hardware, sensores e informações do sistema.
    Centraliza bibliotecas como psutil, GPUtil e platform, isolando o frontend e a bridge destas dependências.
    """
    def __init__(
        self,
        hw_info: Optional[Dict[str, Any]] = None,
        psutil_module=None,
        gpu_provider=None,
        platform_module=None,
        sleep_fn: Optional[Callable[[float], None]] = None,
        hardware_mod=None
    ):
        self._hw_info = hw_info or {}
        
        # Injeção de dependências para testes e abstração
        if psutil_module is None:
            import psutil
            psutil_module = psutil
        if platform_module is None:
            import platform
            platform_module = platform
        if hardware_mod is None:
            from modules import hardware as hw
            hardware_mod = hw
            
        self._psutil = psutil_module
        self._platform = platform_module
        self._sleep = sleep_fn or time.sleep
        self._hardware_mod = hardware_mod
        
        # O provider GPUtil pode não estar disponível em algumas máquinas (módulo opcional)
        if gpu_provider is None:
            try:
                import GPUtil
                gpu_provider = GPUtil
            except ImportError:
                gpu_provider = None
        self._gputil = gpu_provider

    def obter_hardware(self) -> dict:
        return self._hw_info

    def obter_nivel_qualidade_visual(self) -> str:
        return self._hardware_mod.classificar_capacidade_hardware(self._hw_info)

    def obter_metricas_rapidas(self) -> dict:
        try:
            cpu = self._psutil.cpu_percent(interval=0.1)
            mem = self._psutil.virtual_memory()
            freq = self._psutil.cpu_freq()
            return {
                "ok": True,
                "cpu_percent": cpu,
                "ram_percent": round(mem.percent, 1),
                "ram_disponivel_gb": round(mem.available / (1024**3), 1),
                "cpu_freq_mhz": round(freq.current, 0) if freq else None
            }
        except Exception as e:
            logger.exception("Falha ao obter_metricas_rapidas")
            return {
                "ok": False,
                "cpu_percent": 0.0,
                "ram_percent": 0.0,
                "ram_disponivel_gb": 0.0,
                "cpu_freq_mhz": None
            }

    def obter_info_sistema_detalhado(self) -> dict:
        try:
            freq = self._psutil.cpu_freq()
            
            discos = []
            for p in self._psutil.disk_partitions():
                try:
                    uso = self._psutil.disk_usage(p.mountpoint)
                    discos.append({
                        "unidade": p.device,
                        "fstype": p.fstype,
                        "total_gb": round(uso.total / (1024**3), 1),
                        "usado_gb": round(uso.used / (1024**3), 1),
                        "livre_gb": round(uso.free / (1024**3), 1),
                        "percentual": uso.percent
                    })
                except Exception:
                    continue
            
            mem = self._psutil.virtual_memory()
            try:
                swap = self._psutil.swap_memory()
                swap_total = round(swap.total / (1024**3), 1)
                swap_usado = round(swap.used / (1024**3), 1)
            except Exception:
                swap_total = None
                swap_usado = None
            
            boot_time = self._psutil.boot_time()
            uptime_segundos = (datetime.now() - datetime.fromtimestamp(boot_time)).seconds
            horas = uptime_segundos // 3600
            minutos = (uptime_segundos % 3600) // 60
            
            return {
                "ok": True,
                "sistema": {
                    "os": f"{self._platform.system()} {self._platform.release()}",
                    "versao": self._platform.version()[:50],
                    "arquitetura": self._platform.machine(),
                    "uptime": f"{horas}h {minutos}m"
                },
                "cpu": {
                    "modelo": self._hw_info.get("cpu", {}).get("modelo", "N/A"),
                    "nucleos_fisicos": self._psutil.cpu_count(logical=False),
                    "nucleos_logicos": self._psutil.cpu_count(logical=True),
                    "freq_atual": round(freq.current, 0) if freq else None,
                    "freq_max": round(freq.max, 0) if freq and freq.max else None,
                    "freq_min": round(freq.min, 0) if freq and freq.min else None,
                    "arquitetura": self._platform.machine()
                },
                "ram": {
                    "total_gb": round(mem.total / (1024**3), 1),
                    "disponivel_gb": round(mem.available / (1024**3), 1),
                    "usada_gb": round(mem.used / (1024**3), 1),
                    "percentual": round(mem.percent, 1),
                    "swap_total_gb": swap_total,
                    "swap_usado_gb": swap_usado
                },
                "discos": discos,
                "gpus": self._hw_info.get("gpus", [])
            }
        except Exception:
            logger.exception("Falha ao obter_info_sistema_detalhado")
            return {"ok": False, "erro": "Não foi possível coletar as informações do sistema"}

    def obter_metricas_completas(self) -> dict:
        try:
            cpu_total = self._psutil.cpu_percent(interval=0.1)
            cpu_por_nucleo = self._psutil.cpu_percent(interval=None, percpu=True)
            freq = self._psutil.cpu_freq()
            mem = self._psutil.virtual_memory()
            
            io1 = self._psutil.disk_io_counters()
            self._sleep(0.5)
            io2 = self._psutil.disk_io_counters()
            read_mb = round((io2.read_bytes - io1.read_bytes) / (1024**2) / 0.5, 1) if io1 and io2 else 0
            write_mb = round((io2.write_bytes - io1.write_bytes) / (1024**2) / 0.5, 1) if io1 and io2 else 0
            
            gpu_data = None
            if self._gputil:
                try:
                    gpus = self._gputil.getGPUs()
                    if gpus:
                        g = gpus[0]
                        gpu_data = {
                            "nome": g.name,
                            "uso": int(g.load * 100),
                            "temp": int(g.temperature),
                            "vram_usada": int(g.memoryUsed),
                            "vram_total": int(g.memoryTotal)
                        }
                except Exception as ex:
                    logger.warning(f"Erro ao obter dados GPUtil em obter_metricas_completas: {ex}")
            
            return {
                "ok": True,
                "cpu": {
                    "total": cpu_total,
                    "por_nucleo": cpu_por_nucleo,
                    "freq_mhz": round(freq.current, 0) if freq else None,
                    "nucleos": len(cpu_por_nucleo)
                },
                "ram": {
                    "percent": round(mem.percent, 1),
                    "usada_gb": round(mem.used / (1024**3), 1),
                    "total_gb": round(mem.total / (1024**3), 1),
                    "disponivel_gb": round(mem.available / (1024**3), 1)
                },
                "disco": {
                    "leitura_mb": read_mb,
                    "escrita_mb": write_mb
                },
                "gpu": gpu_data
            }
        except Exception:
            logger.exception("Falha ao obter_metricas_completas")
            return {"ok": False, "erro": "Falha na coleta de métricas completas"}

    def obter_gpu_rapida(self) -> dict:
        if not self._gputil:
            return {"ok": False, "gpu": None}
            
        try:
            gpus = self._gputil.getGPUs()
            if gpus:
                g = gpus[0]
                return {
                    "ok": True,
                    "gpu": {
                        "uso": int(g.load * 100),
                        "temp": int(g.temperature),
                        "vram_usada": int(g.memoryUsed),
                        "vram_total": int(g.memoryTotal)
                    }
                }
        except Exception as ex:
            logger.warning(f"Erro ao obter gpu rápida: {ex}")
            
        return {"ok": False, "gpu": None}

    def carregar_hardware_cache(self, progress_callback=None) -> dict:
        hw = self._hardware_mod.obter_hardware_com_cache(progress_callback=progress_callback)
        self._hw_info = hw
        return {"ok": True, "hardware": hw}

    def forcar_rescan_hardware(self, progress_callback=None) -> dict:
        hw = self._hardware_mod.coletar_hardware_completo(progress_callback=progress_callback)
        self._hw_info = hw
        return {"ok": True, "hardware": hw}
