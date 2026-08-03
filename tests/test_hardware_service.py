import pytest
from unittest.mock import MagicMock
from modules.core.hardware_service import HardwareService

class MockPsutil:
    def __init__(self, fail_warmup=False):
        self.warmup_calls = []
        self._fail_warmup = fail_warmup
    def cpu_percent(self, interval=None, percpu=False):
        self.warmup_calls.append("warmup")
        if self._fail_warmup:
            raise RuntimeError("Warmup failed")
        return 25.0
    def virtual_memory(self):
        class Mem:
            percent = 50.0
            available = 4 * 1024**3
        return Mem()
    def boot_time(self):
        return 1600000000

class MockHardwareMod:
    def classificar_capacidade_hardware(self, hw):
        return "alto"
    def obter_hardware_com_cache(self, progress_callback=None):
        return {"fake": "cache"}
    def coletar_hardware_completo(self, progress_callback=None):
        return {"fake": "scan"}

class MockHardwareMetrics:
    def __init__(self, gpus=None):
        self.reset_called = False
        self._gpus = gpus
    def reset_io_counters(self):
        self.reset_called = True
    def coletar_metricas_completas(self):
        return {
            "ok": True,
            "cpu": {"uso_percentual": 25.0},
            "gpus": self._gpus if self._gpus is not None else [{"nome": "Dummy GPU"}]
        }


def test_hardware_service_preparar_metricas():
    mock_ps = MockPsutil()
    mock_metrics = MockHardwareMetrics()
    svc = HardwareService(psutil_module=mock_ps, hardware_metrics_mod=mock_metrics)
    svc.preparar_metricas()
    assert "warmup" in mock_ps.warmup_calls
    assert mock_metrics.reset_called

def test_hardware_service_preparar_metricas_falha_segura():
    mock_ps = MockPsutil(fail_warmup=True)
    svc = HardwareService(psutil_module=mock_ps)
    svc.preparar_metricas()
    assert "warmup" in mock_ps.warmup_calls

def test_hardware_service_nivel_visual():
    svc = HardwareService(hardware_mod=MockHardwareMod())
    res = svc.obter_nivel_qualidade_visual()
    assert res == "alto"

def test_hardware_service_metricas_rapidas():
    svc = HardwareService(psutil_module=MockPsutil())
    res = svc.obter_metricas_rapidas()
    assert res["ok"] is True
    assert res["cpu_percent"] == 25.0
    assert res["ram_percent"] == 50.0

def test_hardware_service_gpu_ausente():
    mock_metrics = MockHardwareMetrics(gpus=[])
    svc = HardwareService(hardware_metrics_mod=mock_metrics)
    res = svc.obter_gpu_rapida()
    assert res["ok"] is True
    assert res["gpu"] is None

def test_hardware_service_metricas_completas():
    mock_metrics = MockHardwareMetrics()
    svc = HardwareService(hardware_metrics_mod=mock_metrics)
    # Precisamos mockar datetime pra não dar erro no boot time real vs timestamp 1600000000?
    # Actually, the uptime logic falls back to a string or 0 if it's negative
    res = svc.obter_metricas_completas()
    assert res["ok"] is True
    assert "uptime" in res
    assert "gpus" in res

def test_hardware_service_info_detalhado():
    mock_metrics = MockHardwareMetrics()
    svc = HardwareService(hardware_metrics_mod=mock_metrics)
    res = svc.obter_info_sistema_detalhado()
    assert res["ok"] is True
    assert "cpu" in res

def test_hardware_service_cache_e_rescan():
    svc = HardwareService(hardware_mod=MockHardwareMod())
    res1 = svc.carregar_hardware_cache()
    assert res1["ok"] is True
    assert res1["hardware"]["fake"] == "cache"
    assert svc.obter_hardware()["fake"] == "cache"
    
    res2 = svc.forcar_rescan_hardware()
    assert res2["ok"] is True
    assert res2["hardware"]["fake"] == "scan"
    assert svc.obter_hardware()["fake"] == "scan"
