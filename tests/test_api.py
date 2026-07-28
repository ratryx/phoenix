import pytest
import time
from modules.gui.api import PhoenixAPI

class MockHardwareService:
    def carregar_hardware_cache(self, progress_callback=None):
        pass
    def forcar_rescan_hardware(self):
        pass
    def obter_hardware(self):
        return {}
    def obter_nivel_qualidade_visual(self):
        return "alto"

class MockWindowController:
    def minimizar(self):
        pass
    def fechar(self):
        pass

class MockRoutineService:
    def executar(self, id_atendimento, nome_cliente, job_context=None):
        pass

class MockJobManager:
    def submit(self, fn, *args, job_id=None, operation_name=None, exclusive_group=None, timeout=None, pass_job_context=False, **kwargs):
        self.last_timeout = timeout
        return "123"
    def update_progress(self, job_id, pct, msg):
        pass
    def get_progress(self, job_id):
        return 0

def test_api_timeout_policies():
    jm = MockJobManager()
    api = PhoenixAPI(hw_info={}, job_manager=jm, hardware_service=MockHardwareService(), window_controller=MockWindowController(), routine_service=MockRoutineService())

    # default
    api.obter_diagnostico()
    assert jm.last_timeout == 30

    # rotina completa
    api.executar_rotina_completa()
    assert jm.last_timeout == 600

    # system_mutation fallback
    api.executar_limpeza()
    assert jm.last_timeout == 180

    # restore point
    api.criar_ponto_restauracao()
    assert jm.last_timeout == 300

    # hardware cache
    api.carregar_hardware_cache()
    assert jm.last_timeout == 45
