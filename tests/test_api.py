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


import time
from modules.gui.jobs import JobManager
from modules.gui_app import iniciar

def test_api_injecao_manager():
    """Valida se a API usa a inst├óncia exata de JobManager, HardwareService e WindowController injetada."""
    manager = JobManager(ttl_seconds=100)
    
    class FakeHardwareService:
        pass
    class FakeWindowController:
        pass
    
    hw_service = FakeHardwareService()
    win_ctrl = FakeWindowController()
    
    api = PhoenixAPI({}, job_manager=manager, hardware_service=hw_service, window_controller=win_ctrl)
    assert api._job_manager is manager
    assert api._hardware_service is hw_service
    assert api._window_controller is win_ctrl
    
    api_default = PhoenixAPI({})
    assert isinstance(api_default._job_manager, JobManager)
    assert type(api_default._hardware_service).__name__ == "HardwareService"
    assert type(api_default._window_controller).__name__ == "WindowController"
    assert type(api_default._routine_service).__name__ == "RoutineService"

def test_api_delegacao_routine_service(monkeypatch):
    """Valida se a API injeta e aciona o RoutineService corretamente sem chamar m├│dulos diretos."""
    class MockRoutineService:
        def __init__(self):
            self.chamadas = []
        def executar(self, id_atendimento, nome_cliente, job_context=None):
            self.chamadas.append((id_atendimento, nome_cliente))
            return {"ok": True, "res": "mockado"}

    mock_routine = MockRoutineService()
    manager = JobManager()
    
    api = PhoenixAPI({}, job_manager=manager, routine_service=mock_routine)
    
    # Chama o endpoint
    res = api.executar_rotina_completa(nome_cliente="Fulano")
    assert "job_id" in res
    
    import time
    time.sleep(0.1)
    
    payload = api.verificar_tarefa(res["job_id"])
    assert payload["status"] == "done"
    assert payload["resultado"] == {"ok": True, "res": "mockado"}
    
    # Valida par├ómetros passados pro servi├ºo
    assert len(mock_routine.chamadas) == 1
    chamada = mock_routine.chamadas[0]
    
    assert chamada[0] == api._id_atendimento
    assert chamada[1] == "Fulano"
    
    job_interno = manager._jobs[res["job_id"]]
    assert job_interno["exclusive_group"] == "system_mutation"

def test_api_delegacao_verificar_tarefa():
    """Valida se verificar_tarefa delega de fato para o JobManager."""
    manager = JobManager()
    api = PhoenixAPI({}, job_manager=manager)
    
    job_id = manager.submit(lambda: {"ok": True})
    time.sleep(0.1)
    
    # Chama pela API
    payload = api.verificar_tarefa(job_id)
    assert payload["status"] == "done"
    assert payload["resultado"]["ok"] is True

def test_api_metodo_assincrono_leitura(monkeypatch):
    """Valida que uma opera├º├úo de leitura (obter_diagnostico) roda em background sem grupo exclusivo."""
    from modules import diagnostico
    monkeypatch.setattr(diagnostico, "coletar_diagnostico_silencioso", lambda: {"diag": 1})
    
    manager = JobManager()
    api = PhoenixAPI({}, job_manager=manager)
    
    res = api.obter_diagnostico()
    assert "job_id" in res
    
    job_id = res["job_id"]
    time.sleep(0.1)
    
    payload = api.verificar_tarefa(job_id)
    assert payload["status"] == "done"
    assert payload["resultado"]["dados"]["diag"] == 1
    
    # Validar que nao utilizou exclusive_group (acessando variaveis do manager por debaixo dos panos)
    job_interno = manager._jobs[job_id]
    assert job_interno["exclusive_group"] is None

def test_api_metodo_assincrono_destrutivo(monkeypatch):
    """Valida que uma opera├º├úo de muta├º├úo utiliza o grupo system_mutation."""
    from modules import limpeza
    monkeypatch.setattr(limpeza, "executar_limpeza_completa", lambda x: 500)
    
    manager = JobManager()
    api = PhoenixAPI({}, job_manager=manager)
    
    res = api.executar_limpeza()
    job_id = res["job_id"]
    
    time.sleep(0.1)
    payload = api.verificar_tarefa(job_id)
    assert payload["status"] == "done"
    
    job_interno = manager._jobs[job_id]
    assert job_interno["exclusive_group"] == "system_mutation"

def test_api_metodo_com_progresso(monkeypatch):
    """Valida que carregar_hardware_cache emite atualiza├º├Áes de progresso no payload e n├úo corrompe sistema."""
    from modules import hardware
    def mock_hw(progress_callback=None):
        if progress_callback:
            progress_callback("GPU Check")
        return {"hw": 1}
        
    monkeypatch.setattr(hardware, "obter_hardware_com_cache", mock_hw)
    
    manager = JobManager()
    api = PhoenixAPI({}, job_manager=manager)
    
    res = api.carregar_hardware_cache()
    job_id = res["job_id"]
    
    # Testa se a mensagem pre-worker "Iniciando detec├º├úo..." entrou em vigor r├ípido (antes do worker)
    payload_inicio = api.verificar_tarefa(job_id)
    
    deadline = time.monotonic() + 5.0
    payload_fim = api.verificar_tarefa(job_id)

    while (
        payload_fim["status"]
        not in {"done", "failed", "cancelled", "timed_out"}
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
        payload_fim = api.verificar_tarefa(job_id)

    assert payload_fim["status"] == "done"
    assert payload_fim["resultado"]["hardware"]["hw"] == 1

def test_api_concorrencia_destrutiva_rejeita(monkeypatch):
    """Testa que duas opera├º├Áes do mesmo grupo exclusivo geram conflito seguro."""
    from modules import limpeza
    import time
    
    def slow_limpeza(id):
        time.sleep(0.3)
        return 100
        
    monkeypatch.setattr(limpeza, "executar_limpeza_completa", slow_limpeza)
    
    manager = JobManager()
    api = PhoenixAPI({}, job_manager=manager)
    
    res1 = api.executar_limpeza()
    job_id1 = res1["job_id"]
    
    # Tenta rodar a mesma (ou outra de mutacao) logo em seguida
    res2 = api.executar_limpeza()
    job_id2 = res2["job_id"]
    
    # job 2 falhou logo de cara
    payload2 = api.verificar_tarefa(job_id2)
    assert payload2["status"] == "failed"
    assert payload2["resultado"]["ok"] is False
    assert "está em execução" in payload2["resultado"]["erro"]
    assert "system_mutation" not in payload2["resultado"].get("erro", "")
    assert "system_mutation" not in payload2["resultado"].get("detalhe", "")
    assert payload2["resultado"]["detalhe"] == "Por favor, aguarde a conclusão da tarefa atual."
    
    # job 1 ainda estara executando ou terminar├í
    time.sleep(0.4)
    payload1 = api.verificar_tarefa(job_id1)
    assert payload1["status"] == "done"

def test_janela_nao_serializada():
    api = PhoenixAPI({})
    import inspect
    public_attrs = [a for a in dir(api) if not a.startswith('_') and not callable(getattr(api, a))]
    assert "janela" not in public_attrs
    assert "window_controller" not in public_attrs
    
    # Valida dicion├írio interno explicitamente
    dict_api = api.__dict__
    assert "_janela" not in dict_api
    assert "_window" not in dict_api
    assert "_is_dragging" not in dict_api
    assert "_drag_start_mouse_x" not in dict_api
    assert "jobs" not in dict_api
    
    # E via hasattr
    assert not hasattr(api, "_janela")

def test_compatibilidade_imports():
    """Valida se o re-export de gui_app.py aponta para a mesma classe de gui.api e sem efeitos colaterais."""
    from modules.gui.api import PhoenixAPI as NewAPI
    from modules.gui_app import PhoenixAPI as LegacyAPI
    assert NewAPI is LegacyAPI

class MockHardwareService:
    def obter_hardware(self): return {"tipo": "hardware"}
    def obter_nivel_qualidade_visual(self): return "alto"
    def obter_metricas_rapidas(self): return {"tipo": "rapida"}
    def obter_info_sistema_detalhado(self): return {"tipo": "detalhado"}
    def obter_metricas_completas(self): return {"tipo": "completa"}
    def obter_gpu_rapida(self): return {"tipo": "gpu"}
    
    def carregar_hardware_cache(self, progress_callback=None):
        if progress_callback: progress_callback("Final")
        return {"ok": True}
        
    def forcar_rescan_hardware(self, progress_callback=None):
        return {"ok": True}

def test_api_delegacao_hardware_sincrono():
    """Testa se os m├®todos s├¡ncronos delegam para o HardwareService sem criar jobs."""
    api = PhoenixAPI({}, hardware_service=MockHardwareService())
    
    assert api.obter_hardware() == {"tipo": "hardware"}
    assert api.obter_nivel_qualidade_visual() == "alto"
    assert api.obter_metricas_rapidas() == {"tipo": "rapida"}
    assert api.obter_info_sistema_detalhado() == {"tipo": "detalhado"}
    assert api.obter_metricas_completas() == {"tipo": "completa"}
    assert api.obter_gpu_rapida() == {"tipo": "gpu"}

def test_api_delegacao_hardware_assincrono():
    """Testa se cache e rescan rodam via JobManager mas delegam ao HardwareService."""
    api = PhoenixAPI({}, hardware_service=MockHardwareService())
    
    res_cache = api.carregar_hardware_cache()
    assert "job_id" in res_cache
    time.sleep(0.1)
    
    payload = api.verificar_tarefa(res_cache["job_id"])
    assert payload["status"] == "done"
    assert payload["resultado"]["ok"] is True
    # Como rodamos o cb "Final", deve ter batido no progress callback:
    assert payload.get("progresso") == 100
    
    res_rescan = api.forcar_rescan_hardware()
    assert "job_id" in res_rescan
    time.sleep(0.1)
    payload_rescan = api.verificar_tarefa(res_rescan["job_id"])
    assert payload_rescan["status"] == "done"
    assert payload_rescan["resultado"]["ok"] is True

def test_api_delegacao_janela():
    """Testa se os m├®todos da janela s├úo delegados pro WindowController."""
    class FakeWindowController:
        def __init__(self):
            self.calls = []
        def iniciar_drag(self, a, b, c, d): self.calls.append(("iniciar_drag", a, b, c, d))
        def mover_janela(self, a, b): self.calls.append(("mover_janela", a, b))
        def parar_drag(self): self.calls.append(("parar_drag",))
        def minimizar(self): self.calls.append(("minimizar",))
        def fechar(self): self.calls.append(("fechar",))

    win_ctrl = FakeWindowController()
    api = PhoenixAPI({}, window_controller=win_ctrl)
    
    api.iniciar_drag(1, 2, 3, 4)
    api.mover_janela(5, 6)
    api.parar_drag()
    api.minimizar_janela()
    api.fechar_janela()
    
    assert win_ctrl.calls == [
        ("iniciar_drag", 1, 2, 3, 4),
        ("mover_janela", 5, 6),
        ("parar_drag",),
        ("minimizar",),
        ("fechar",)
    ]

def test_iniciar_gui_app(monkeypatch):
    """
    Testa que a inicializa├º├úo n├úo abre janela real, usa a mesma inst├óncia de HardwareService
    e WindowController, e chama set_window() com a janela criada pelo webview.
    """
    import modules.gui_app
    import webview
    
    class DummyWindow:
        pass
    
    fake_janela = DummyWindow()
    monkeypatch.setattr(webview, "create_window", lambda **kw: fake_janela)
    monkeypatch.setattr(webview, "start", lambda **kw: None)
    
    historico_criacoes_hw = []
    class FakeHardwareService:
        def __init__(self, hw_info=None):
            self.hw_info = hw_info
            self.preparado = False
            historico_criacoes_hw.append(self)
        def preparar_metricas(self):
            self.preparado = True

    historico_criacoes_win = []
    class FakeWindowController:
        def __init__(self):
            self.janela_setada = None
            historico_criacoes_win.append(self)
        def set_window(self, win):
            self.janela_setada = win
            
    import modules.core.hardware_service
    import modules.gui.window_controller
    monkeypatch.setattr(modules.core.hardware_service, "HardwareService", FakeHardwareService)
    monkeypatch.setattr(modules.gui.window_controller, "WindowController", FakeWindowController)

    iniciar()

    assert len(historico_criacoes_hw) == 1
    assert historico_criacoes_hw[0].preparado is True
    
    assert len(historico_criacoes_win) == 1
    assert historico_criacoes_win[0].janela_setada is fake_janela


def test_nested_cancellation_network_reset(monkeypatch):
    from modules.gui.api import PhoenixAPI
    from modules.core.exceptions import JobCancelledError
    from modules.gui.jobs import JobManager
    
    jm = JobManager()
    api = PhoenixAPI(hw_info={}, job_manager=jm)
    
    # Mock otimizacao.executar_otimizacao_gaming to return COMMAND_CANCELLED
    def mock_gaming(*args, **kwargs):
        return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
        
    monkeypatch.setattr("modules.otimizacao.executar_otimizacao_gaming", mock_gaming)
    
    res = api.executar_otimizacao_gaming(resetar_rede=True)
    job_id = res["job_id"]
    
    # Check if job fails with JobCancelledError
    final_res = jm.consultar(job_id)
    import time
    while final_res["status"] in ("pending", "running"):
        time.sleep(0.1)
        final_res = jm.consultar(job_id)
        
    assert final_res["status"] == "cancelled"
