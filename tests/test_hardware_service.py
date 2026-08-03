import pytest
import threading
from unittest.mock import MagicMock
from modules.core.hardware_service import HardwareService

class MockPsutil:
    def __init__(self, fail_warmup=False):
        self.warmup_calls = []
        self._fail_warmup = fail_warmup

    def cpu_percent(self, interval=None, percpu=False):
        # Não é mais usado diretamente em warmup
        if percpu:
            return [25.0, 25.0]
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

    def coletar_metricas_completas(self, psutil_module=None):
        return {
            "ok": True,
            "cpu": {"uso_percentual": 25.0},
            "gpus": self._gpus if self._gpus is not None else [{"nome": "Dummy GPU"}]
        }

    def obter_uso_cpu(self, psutil_module=None):
        return 25.0, [25.0, 25.0]

    def obter_metricas_gpu(self):
        return self._gpus if self._gpus is not None else [{"nome": "Dummy GPU"}]

def test_hardware_service_preparar_metricas():
    mock_ps = MockPsutil()
    mock_metrics = MockHardwareMetrics()
    svc = HardwareService(psutil_module=mock_ps, hardware_metrics_mod=mock_metrics)
    svc.preparar_metricas()
    assert mock_metrics.reset_called

def test_hardware_service_preparar_metricas_falha_segura():
    # boot_time falhando
    mock_ps = MockPsutil(fail_warmup=True)
    def fail_boot():
        raise RuntimeError("Fail")
    mock_ps.boot_time = fail_boot
    svc = HardwareService(psutil_module=mock_ps)
    svc.preparar_metricas()
    assert svc._boot_time is None

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

class DeterministicMockHardwareMod:
    def __init__(self, should_fail=False):
        self.call_count = 0
        self.should_fail = should_fail
        self.enter_event = threading.Event()
        self.resume_event = threading.Event()

    def coletar_hardware_completo(self, progress_callback=None):
        self.call_count += 1
        self.enter_event.set()
        self.resume_event.wait()
        if self.should_fail:
            raise RuntimeError("Erro forcado na varredura")
        return {"fake": "scan_deterministic"}

def test_hardware_service_single_flight():
    mock_hw = DeterministicMockHardwareMod()
    svc = HardwareService(hardware_mod=mock_hw)
    results = []

    def worker():
        results.append(svc.forcar_rescan_hardware())

    t1 = threading.Thread(target=worker)
    t1.start()

    # Wait for t1 to enter the mock and block
    assert mock_hw.enter_event.wait(timeout=2.0)

    # Start t2 while t1 is active
    t2 = threading.Thread(target=worker)
    t2.start()

    # Release the lock
    mock_hw.resume_event.set()

    t1.join(timeout=2.0)
    t2.join(timeout=2.0)

    assert len(results) == 2
    assert results[0] == results[1]
    assert results[0]["ok"] is True
    assert results[0]["hardware"]["fake"] == "scan_deterministic"
    assert mock_hw.call_count == 1

def test_hardware_service_single_flight_failure():
    mock_hw = DeterministicMockHardwareMod(should_fail=True)
    svc = HardwareService(hardware_mod=mock_hw)
    results = []

    def worker():
        results.append(svc.forcar_rescan_hardware())

    t1 = threading.Thread(target=worker)
    t1.start()

    assert mock_hw.enter_event.wait(timeout=2.0)

    t2 = threading.Thread(target=worker)
    t2.start()

    mock_hw.resume_event.set()

    t1.join(timeout=2.0)
    t2.join(timeout=2.0)

    assert len(results) == 2
    assert results[0] == results[1]
    assert results[0]["ok"] is False
    assert results[0]["codigo"] == "HARDWARE_RESCAN_FAILED"
    assert mock_hw.call_count == 1
    assert svc._rescan_promise is None

    # A third call should execute a new collect and succeed (mocking it succeeds this time)
    mock_hw.should_fail = False
    mock_hw.enter_event.clear()
    mock_hw.resume_event.set() # Don't block the third call

    res3 = svc.forcar_rescan_hardware()
    assert res3["ok"] is True
    assert res3["hardware"]["fake"] == "scan_deterministic"
    assert mock_hw.call_count == 2

def test_hardware_service_cpu_metrics_integration():
    """
    Cobre: primeira coleta, mesma instância, serviço recriado,
    payload (Início / HWMonitor), regressões.
    """
    mock_ps = MockPsutil()
    mock_ps.cpu_percent = MagicMock(return_value=[20.0, 80.0]) # Média 50.0

    # Para coletar_metricas_completas, o psutil_module precisa ser repassado
    # Importante: O MockHardwareMetrics atual no teste retorna hardcoded "25.0".
    # Como queremos testar a integração REAL com hardware_metrics,
    # não usaremos o MockHardwareMetrics aqui. Usaremos o original.
    import modules.core.hardware_metrics as real_metrics

    # Mock disk e mem para não falhar
    mock_ps.disk_io_counters = MagicMock(return_value=None)
    class Mem:
        percent = 50.0
        used = 2 * 1024**3
        available = 4 * 1024**3
    mock_ps.virtual_memory = MagicMock(return_value=Mem())
    mock_ps.cpu_freq = MagicMock(return_value=None)

    # Serviço criado (primeira coleta)
    svc1 = HardwareService(psutil_module=mock_ps, hardware_metrics_mod=real_metrics)
    rapidas1 = svc1.obter_metricas_rapidas() # Início
    completas1 = svc1.obter_metricas_completas() # HWMonitor

    # Deve ser 50.0 (média de 20 e 80)
    assert rapidas1["cpu_percent"] == 50.0
    assert completas1["cpu"]["uso_percentual"] == 50.0

    # Mesma instância (coletas consecutivas)
    mock_ps.cpu_percent.return_value = [10.0, 10.0]
    rapidas2 = svc1.obter_metricas_rapidas()
    assert rapidas2["cpu_percent"] == 10.0

    # Serviço recriado
    mock_ps.cpu_percent.return_value = [30.0, 30.0]
    svc2 = HardwareService(psutil_module=mock_ps, hardware_metrics_mod=real_metrics)
    rapidas3 = svc2.obter_metricas_rapidas()
    assert rapidas3["cpu_percent"] == 30.0

    # Ausência de regressões em RAM e outros
    assert rapidas1["ram_percent"] == 50.0
    assert completas1["memoria"]["percentual_uso"] == 50.0

def test_hardware_service_gpu_rapida_nao_chama_cpu():
    import modules.core.hardware_metrics as real_metrics
    mock_ps = MockPsutil()
    mock_ps.cpu_percent = MagicMock()

    svc = HardwareService(psutil_module=mock_ps, hardware_metrics_mod=real_metrics)
    res = svc.obter_gpu_rapida()

    mock_ps.cpu_percent.assert_not_called()
    assert res["ok"] is True

def test_api_hardware_service_integration():
    import modules.core.hardware_metrics as real_metrics
    from modules.gui.api import PhoenixAPI

    mock_ps = MockPsutil()
    mock_ps.cpu_percent = MagicMock(return_value=[15.0, 15.0])
    mock_ps.disk_io_counters = MagicMock(return_value=None)
    class Mem:
        percent = 50.0
        used = 2 * 1024**3
        available = 4 * 1024**3
    mock_ps.virtual_memory = MagicMock(return_value=Mem())
    mock_ps.cpu_freq = MagicMock(return_value=None)

    svc = HardwareService(psutil_module=mock_ps, hardware_metrics_mod=real_metrics)

    # Inicializa a API injetando o serviço integrado de hardware
    api = PhoenixAPI(
        hw_info={},
        hardware_service=svc
    )

    # O payload da página Início consome obter_metricas_rapidas
    res_inicio = api.obter_metricas_rapidas()
    assert res_inicio["ok"] is True
    assert res_inicio["cpu_percent"] == 15.0

    # O payload do HWMonitor consome obter_metricas_completas
    res_hw = api.obter_metricas_completas()
    assert res_hw["ok"] is True
    assert res_hw["cpu"]["uso_percentual"] == 15.0

def test_hardware_service_dynamic_capabilities():
    import sys
    from unittest.mock import patch, MagicMock
    
    inventario = {
        "cpu": {"modelo": "Fake CPU"},
        "memoria": {"total_instalada_gb": 16}
    }
    
    mock_gputil = MagicMock()
    mock_gputil.getGPUs.return_value = ["GPU1"]
    
    mock_gputil_empty = MagicMock()
    mock_gputil_empty.getGPUs.return_value = []
    
    mock_gputil_fail = MagicMock()
    mock_gputil_fail.getGPUs.side_effect = Exception("Fail")
    
    mock_ps = MockPsutil()
    mock_ps.cpu_percent = MagicMock(return_value=[15.0])
    
    # 1. GPUs existem
    with patch.dict(sys.modules, {"GPUtil": mock_gputil}):
        svc1 = HardwareService(hw_info=inventario.copy(), psutil_module=mock_ps)
        assert svc1.obter_hardware()["capacidades"]["metricas_gpu_disponiveis"] is True
        
    # 2. Sem GPUs
    with patch.dict(sys.modules, {"GPUtil": mock_gputil_empty}):
        svc2 = HardwareService(hw_info=inventario.copy(), psutil_module=mock_ps)
        assert svc2.obter_hardware()["capacidades"]["metricas_gpu_disponiveis"] is False
        
    # 3. Falha no GPUtil
    with patch.dict(sys.modules, {"GPUtil": mock_gputil_fail}):
        svc3 = HardwareService(hw_info=inventario.copy(), psutil_module=mock_ps)
        assert svc3.obter_hardware()["capacidades"]["metricas_gpu_disponiveis"] is False
        
    # 4. Confirme que o dicionario original injetado continua sem capacidades dinâmicas
    # O HardwareService deve operar em uma cópia.
    original_injetado = inventario.copy()
    with patch.dict(sys.modules, {"GPUtil": mock_gputil}):
        svc4 = HardwareService(hw_info=original_injetado, psutil_module=mock_ps)
        assert svc4.obter_hardware()["capacidades"]["metricas_gpu_disponiveis"] is True
        assert "capacidades" not in original_injetado
