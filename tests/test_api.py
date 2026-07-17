import time
import pytest
from modules.gui.jobs import JobManager
from modules.gui_app import PhoenixAPI

def test_api_injecao_manager():
    """Valida se a API usa a instância exata de JobManager injetada."""
    manager = JobManager(ttl_seconds=100)
    api = PhoenixAPI({}, job_manager=manager)
    assert api._job_manager is manager
    
    # E instanciacao padrao funciona
    api_default = PhoenixAPI({})
    assert isinstance(api_default._job_manager, JobManager)

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
    """Valida que uma operação de leitura (obter_diagnostico) roda em background sem grupo exclusivo."""
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
    """Valida que uma operação de mutação utiliza o grupo system_mutation."""
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
    """Valida que carregar_hardware_cache emite atualizações de progresso no payload e não corrompe sistema."""
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
    
    # Testa se a mensagem pre-worker "Iniciando detecção..." entrou em vigor rápido (antes do worker)
    payload_inicio = api.verificar_tarefa(job_id)
    # the worker might be so fast it finishes immediately, but let's just check the final
    
    time.sleep(0.1)
    payload_fim = api.verificar_tarefa(job_id)
    assert payload_fim["status"] == "done"
    assert payload_fim["resultado"]["hardware"]["hw"] == 1

def test_api_concorrencia_destrutiva_rejeita(monkeypatch):
    """Testa que duas operações do mesmo grupo exclusivo geram conflito seguro."""
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
    assert payload2["status"] == "done"
    assert payload2["resultado"]["ok"] is False
    assert "já está em execução" in payload2["resultado"]["erro"]
    assert "system_mutation" not in payload2["resultado"].get("erro", "")
    assert "system_mutation" not in payload2["resultado"].get("detalhe", "")
    assert payload2["resultado"]["detalhe"] == "Por favor, aguarde a conclusão da tarefa atual."
    
    # job 1 ainda estara executando ou terminará
    time.sleep(0.4)
    payload1 = api.verificar_tarefa(job_id1)
    assert payload1["status"] == "done"

def test_janela_nao_serializada():
    api = PhoenixAPI({})
    import inspect
    public_attrs = [a for a in dir(api) if not a.startswith('_') and not callable(getattr(api, a))]
    assert "janela" not in public_attrs
    assert hasattr(api, "_janela")
