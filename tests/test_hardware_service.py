import pytest
from modules.core.hardware_service import HardwareService

class DummyGPU:
    def __init__(self):
        self.name = "Dummy GPU"
        self.load = 0.5
        self.temperature = 60
        self.memoryUsed = 1024
        self.memoryTotal = 4096

class MockGPUtil:
    def __init__(self, gpus=None, fail=False):
        self._gpus = gpus if gpus is not None else [DummyGPU()]
        self._fail = fail
    def getGPUs(self):
        if self._fail:
            raise RuntimeError("GPU fail")
        return self._gpus

class MockPsutil:
    def __init__(self, fail_warmup=False):
        self.cpu_count_val = 4
        self.warmup_calls = []
        self._fail_warmup = fail_warmup
    def cpu_percent(self, interval=None, percpu=False):
        if interval is None and not percpu:
            self.warmup_calls.append("warmup")
            if self._fail_warmup:
                raise RuntimeError("Warmup failed")
            return 0.0
        if percpu:
            return [10.0, 20.0, 30.0, 40.0]
        return 25.0
    def virtual_memory(self):
        class Mem:
            percent = 50.0
            available = 4 * 1024**3
            total = 8 * 1024**3
            used = 4 * 1024**3
        return Mem()
    def cpu_freq(self):
        class Freq:
            current = 3000
            max = 4000
            min = 1000
        return Freq()
    def disk_partitions(self):
        class Part:
            device = "C:\\"
            mountpoint = "C:\\"
            fstype = "NTFS"
        return [Part()]
    def disk_usage(self, path):
        class Usage:
            total = 500 * 1024**3
            used = 100 * 1024**3
            free = 400 * 1024**3
            percent = 20.0
        return Usage()
    def swap_memory(self):
        class Swap:
            total = 2 * 1024**3
            used = 1 * 1024**3
        return Swap()
    def boot_time(self):
        return 1600000000
    def cpu_count(self, logical=False):
        return self.cpu_count_val
    def disk_io_counters(self):
        class IO:
            read_bytes = 1000000
            write_bytes = 500000
        return IO()

class MockPlatform:
    def system(self): return "Windows"
    def release(self): return "10"
    def version(self): return "10.0.19041"
    def machine(self): return "AMD64"

class MockHardwareMod:
    def classificar_capacidade_hardware(self, hw):
        return "alto"
    def obter_hardware_com_cache(self, progress_callback=None):
        if progress_callback: progress_callback("Fake progress")
        return {"fake": "cache"}
    def coletar_hardware_completo(self, progress_callback=None):
        if progress_callback: progress_callback("Fake scan")
        return {"fake": "scan"}


def test_hardware_service_preparar_metricas():
    mock_ps = MockPsutil()
    svc = HardwareService(psutil_module=mock_ps)
    svc.preparar_metricas()
    assert "warmup" in mock_ps.warmup_calls

def test_hardware_service_preparar_metricas_falha_segura():
    mock_ps = MockPsutil(fail_warmup=True)
    svc = HardwareService(psutil_module=mock_ps)
    # Nao deve levantar excecao
    svc.preparar_metricas()
    assert "warmup" in mock_ps.warmup_calls

def test_hardware_service_nivel_visual():
    svc = HardwareService(hardware_mod=MockHardwareMod())
    res = svc.obter_nivel_qualidade_visual()
    assert res == "alto"

def test_hardware_service_metricas_rapidas():
    svc = HardwareService(
        psutil_module=MockPsutil(),
        gpu_provider=MockGPUtil(),
        platform_module=MockPlatform(),
        hardware_mod=MockHardwareMod()
    )
    res = svc.obter_metricas_rapidas()
    assert res["ok"] is True
    assert res["cpu_percent"] == 25.0
    assert res["ram_percent"] == 50.0
    assert res["cpu_freq_mhz"] == 3000

def test_hardware_service_gpu_ausente():
    svc = HardwareService(
        psutil_module=MockPsutil(),
        gpu_provider=MockGPUtil(gpus=[]),
    )
    res = svc.obter_gpu_rapida()
    assert res["ok"] is False
    assert res["gpu"] is None

def test_hardware_service_gpu_falha_nao_derruba():
    svc = HardwareService(
        psutil_module=MockPsutil(),
        gpu_provider=MockGPUtil(fail=True),
    )
    res = svc.obter_gpu_rapida()
    assert res["ok"] is False
    assert res["gpu"] is None

def test_hardware_service_metricas_completas():
    # Testa sleep mock e calculos
    sleep_calls = []
    def mock_sleep(t): sleep_calls.append(t)
    
    svc = HardwareService(
        psutil_module=MockPsutil(),
        gpu_provider=MockGPUtil(),
        sleep_fn=mock_sleep
    )
    res = svc.obter_metricas_completas()
    assert res["ok"] is True
    assert sleep_calls == [0.5]
    assert len(res["cpu"]["por_nucleo"]) == 4
    assert res["disco"]["leitura_mb"] == 0.0 # Delta eh zero nesse mock simples

def test_hardware_service_info_detalhado():
    svc = HardwareService(
        psutil_module=MockPsutil(),
        platform_module=MockPlatform()
    )
    res = svc.obter_info_sistema_detalhado()
    assert res["ok"] is True
    assert res["sistema"]["os"] == "Windows 10"
    assert res["sistema"]["arquitetura"] == "AMD64"
    assert res["cpu"]["nucleos_fisicos"] == 4
    assert res["ram"]["percentual"] == 50.0

def test_hardware_service_cache_e_rescan():
    svc = HardwareService(hardware_mod=MockHardwareMod())
    
    msgs = []
    def prog(m): msgs.append(m)
    
    res1 = svc.carregar_hardware_cache(progress_callback=prog)
    assert res1["ok"] is True
    assert res1["hardware"]["fake"] == "cache"
    assert "Fake progress" in msgs
    
    res2 = svc.forcar_rescan_hardware()
    assert res2["ok"] is True
    assert res2["hardware"]["fake"] == "scan"
