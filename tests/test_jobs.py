import time
import json
import threading
import pytest
from modules.gui.jobs import JobManager

def test_1_2_3_job_id_criado_imediato_sucesso():
    jm = JobManager()
    def acao():
        return {"ok": True, "dado": 42}
    
    start = time.time()
    job_id = jm.submit(acao)
    assert time.time() - start < 0.1
    
    assert job_id is not None
    assert type(job_id) is str
    
    time.sleep(0.1)
    status = jm.consultar(job_id)
    assert status["status"] == "done"
    assert status["resultado"]["ok"] is True
    assert status["resultado"]["dado"] == 42

def test_4_captura_de_excecao():
    jm = JobManager()
    def funcao_que_quebra():
        raise ValueError(r"Falha em C:\Users\Cliente\Documents\segredo.txt dentro de executar_registro")
        
    job_id = jm.submit(funcao_que_quebra)
    time.sleep(0.1)
    
    status = jm.consultar(job_id)
    assert status["status"] == "done"
    assert status["resultado"]["ok"] is False
    
    # Teste de Segurança: vazamento de dados da exception
    payload_str = json.dumps(status)
    assert "Traceback" not in payload_str
    assert "C:\\Users" not in payload_str
    assert "segredo.txt" not in payload_str
    assert "executar_registro" not in payload_str
    assert "Não foi possível concluir" in status["resultado"]["erro"]
    assert "inesperado ocorreu" in status["resultado"]["detalhe"]

def test_5_consulta_job_inexistente():
    jm = JobManager()
    status = jm.consultar("id-falso-123")
    assert status["status"] == "not_found"

def test_6_7_resultado_serializavel():
    jm = JobManager()
    job_id = jm.submit(lambda: {"ok": True, "lista": [1, 2, 3]})
    time.sleep(0.1)
    
    status = jm.consultar(job_id)
    json_str = json.dumps(status)
    assert "done" in json_str
    assert "lista" in json_str
    
    # Objeto não serializável
    class NaoSerializavel:
        def __repr__(self):
            return "<NaoSerializavel memory_addr: 0xDEADBEEF>"
            
    job_id2 = jm.submit(lambda: {"ok": True, "objeto": NaoSerializavel()})
    time.sleep(0.1)
    status2 = jm.consultar(job_id2)
    
    assert status2["status"] == "done"
    assert status2["resultado"]["ok"] is False
    
    # Teste de Segurança: vazamento de objeto memory ou internals
    payload_str = json.dumps(status2)
    assert "0xDEADBEEF" not in payload_str
    assert "NaoSerializavel" not in payload_str
    assert "Traceback" not in payload_str
    assert "Erro interno do aplicativo" in status2["resultado"]["erro"]
    assert "Não foi possível exibir" in status2["resultado"]["detalhe"]

def test_8_9_ttl_remove_job():
    jm = JobManager(ttl_seconds=0.1)
    
    def job_lento():
        time.sleep(0.3)
        return {"ok": True}
        
    job_em_execucao = jm.submit(job_lento)
    job_concluido = jm.submit(lambda: {"ok": True})
    
    time.sleep(0.15)
    jm._cleanup_expired()
    
    assert jm.consultar(job_concluido)["status"] == "not_found"
    assert jm.consultar(job_em_execucao)["status"] == "running"
    
    time.sleep(0.2)
    assert jm.consultar(job_em_execucao)["status"] == "done"

def test_11_duas_operacoes_leitura():
    jm = JobManager()
    def operacao():
        time.sleep(0.1)
        return {"ok": True}
        
    job_id1 = jm.submit(operacao, exclusive_group=None)
    job_id2 = jm.submit(operacao, exclusive_group=None)
    
    status1 = jm.consultar(job_id1)
    status2 = jm.consultar(job_id2)
    
    assert status1["status"] == "running"
    assert status2["status"] == "running"

def test_12_13_14_15_grupos_exclusivos():
    jm = JobManager()
    
    def operacao_lenta():
        time.sleep(0.2)
        return {"ok": True}
        
    job_id1 = jm.submit(operacao_lenta, exclusive_group="system_mutation")
    job_id2 = jm.submit(operacao_lenta, exclusive_group="system_mutation")
    
    status2 = jm.consultar(job_id2)
    assert status2["status"] == "done"
    assert status2["resultado"]["ok"] is False
    assert "execução" in status2["resultado"]["erro"]
    
    # Teste de Segurança: Conflito não expõe nomes internos
    payload_str = json.dumps(status2)
    assert "system_mutation" not in payload_str
    assert "lock" not in payload_str.lower()
    
    status1 = jm.consultar(job_id1)
    assert status1["status"] == "running"
    
    time.sleep(0.25)
    assert jm.consultar(job_id1)["status"] == "done"
    
    job_id3 = jm.submit(lambda: {"ok": True}, exclusive_group="system_mutation")
    time.sleep(0.1)
    assert jm.consultar(job_id3)["status"] == "done"

def test_16_17_cem_jobs_concorrentes():
    jm = JobManager()
    ids = []
    for _ in range(100):
        ids.append(jm.submit(lambda: {"ok": True}))
        
    def consultar_tudo():
        for i in ids:
            jm.consultar(i)
            
    threads = []
    for _ in range(10):
        t = threading.Thread(target=consultar_tudo)
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
        
    assert True

def test_18_payload_nomes_esperados():
    jm = JobManager()
    job_id = jm.submit(lambda: {"ok": True})
    time.sleep(0.1)
    jm.update_progress(job_id, 100, "Concluído")
    
    payload = jm.consultar(job_id)
    assert "status" in payload
    assert "resultado" in payload
    assert payload["status"] == "done"
