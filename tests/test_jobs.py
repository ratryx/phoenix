import time
import json
from modules.gui_app import PhoenixAPI, _tarefas

def get_mock_api():
    return PhoenixAPI({"cpu": {}, "ram": {}, "gpus": []})

def test_job_id_criado():
    api = get_mock_api()
    # Mocking uma função rápida
    res = api._iniciar_job(lambda: {"ok": True})
    
    assert "job_id" in res
    assert res["job_id"] in _tarefas
    assert _tarefas[res["job_id"]]["status"] in ["running", "done"]

def test_job_bem_sucedido():
    api = get_mock_api()
    res = api._iniciar_job(lambda: {"ok": True, "dado": 42})
    job_id = res["job_id"]
    
    # Aguarda a thread concluir (teste rápido)
    time.sleep(0.1)
    
    status = api.verificar_tarefa(job_id)
    assert status["status"] == "done"
    assert status["resultado"]["ok"] is True
    assert status["resultado"]["dado"] == 42

def test_job_excecao_nao_derruba():
    api = get_mock_api()
    
    def funcao_que_quebra():
        raise ValueError("Erro simulado")
        
    res = api._iniciar_job(funcao_que_quebra)
    job_id = res["job_id"]
    
    time.sleep(0.1)
    
    status = api.verificar_tarefa(job_id)
    assert status["status"] == "done"
    assert status["resultado"]["ok"] is False
    assert "Erro simulado" in status["resultado"]["erro"]
    assert "Traceback" in status["resultado"]["detalhe"]

def test_consulta_job_inexistente():
    api = get_mock_api()
    status = api.verificar_tarefa("id-falso-123")
    assert status["status"] == "not_found"

def test_resultado_serializavel():
    api = get_mock_api()
    res = api._iniciar_job(lambda: {"ok": True, "lista": [1, 2, 3]})
    job_id = res["job_id"]
    time.sleep(0.1)
    
    status = api.verificar_tarefa(job_id)
    # Tenta serializar
    json_str = json.dumps(status)
    assert "done" in json_str
    assert "lista" in json_str
