import time
import json
import threading
import pytest
from modules.gui.jobs import JobManager, JobContext
from modules.core.exceptions import JobCancelledError

def test_1_2_3_job_id_criado_imediato_sucesso():
    jm = JobManager(watchdog_interval=0.1)
    
    ev_started = threading.Event()
    ev_can_finish = threading.Event()
    
    def acao():
        ev_started.set()
        ev_can_finish.wait()
        return {"ok": True, "dado": 42}
    
    job_id = jm.submit(acao)
    assert type(job_id) is str
    
    ev_started.wait(2.0)
    ev_can_finish.set()
    
    # Wait for completion
    for _ in range(20):
        status = jm.consultar(job_id)
        if status["status"] == "done":
            break
        time.sleep(0.05)
        
    assert status["status"] == "done"
    assert status["resultado"]["ok"] is True
    assert status["resultado"]["dado"] == 42
    jm.shutdown()

def test_4_captura_de_excecao():
    jm = JobManager(watchdog_interval=0.1)
    
    ev = threading.Event()
    def funcao_que_quebra():
        ev.set()
        raise ValueError(r"Falha em C:\Users\Cliente\Documents\segredo.txt dentro de executar_registro")
        
    job_id = jm.submit(funcao_que_quebra)
    ev.wait(2.0)
    
    for _ in range(20):
        status = jm.consultar(job_id)
        if status["status"] == "failed":
            break
        time.sleep(0.05)
        
    assert status["status"] == "failed"
    assert status["resultado"]["ok"] is False
    assert status["resultado"]["codigo"] == "JOB_INTERNAL_ERROR"
    
    # Teste de Segurança
    payload_str = json.dumps(status)
    assert "Traceback" not in payload_str
    assert "C:\\Users" not in payload_str
    assert "segredo.txt" not in payload_str
    assert "executar_registro" not in payload_str
    jm.shutdown()

def test_5_consulta_job_inexistente():
    jm = JobManager(watchdog_interval=0.1)
    status = jm.consultar("id-falso-123")
    assert status["status"] == "not_found"
    jm.shutdown()

def test_6_7_resultado_serializavel():
    jm = JobManager(watchdog_interval=0.1)
    
    ev = threading.Event()
    def success():
        ev.set()
        return {"ok": True, "lista": [1, 2, 3]}
    job_id = jm.submit(success)
    ev.wait(2.0)
    
    for _ in range(20):
        if jm.consultar(job_id)["status"] == "done": break
        time.sleep(0.05)
        
    status = jm.consultar(job_id)
    assert "lista" in json.dumps(status)
    
    # Objeto não serializável
    class NaoSerializavel:
        def __repr__(self):
            return "<NaoSerializavel memory_addr: 0xDEADBEEF>"
            
    ev2 = threading.Event()
    def broken():
        ev2.set()
        return {"ok": True, "objeto": NaoSerializavel()}
    job_id2 = jm.submit(broken)
    ev2.wait(2.0)
    
    for _ in range(20):
        if jm.consultar(job_id2)["status"] == "failed": break
        time.sleep(0.05)
        
    status2 = jm.consultar(job_id2)
    assert status2["status"] == "failed"
    assert status2["resultado"]["codigo"] == "JOB_RESULT_INVALID"
    payload_str = json.dumps(status2)
    assert "0xDEADBEEF" not in payload_str
    assert "NaoSerializavel" not in payload_str
    jm.shutdown()

def test_8_9_ttl_remove_job():
    jm = JobManager(ttl_seconds=0.1, max_retained_jobs=10, watchdog_interval=0.1)
    
    ev_start = threading.Event()
    ev_finish = threading.Event()
    
    def job_lento():
        ev_start.set()
        ev_finish.wait()
        return {"ok": True}
        
    ev2 = threading.Event()
    def rapido():
        ev2.set()
        return {"ok": True}
        
    job_em_execucao = jm.submit(job_lento)
    job_concluido = jm.submit(rapido)
    
    ev_start.wait(2.0)
    ev2.wait(2.0)
    
    for _ in range(20):
        if jm.consultar(job_concluido)["status"] == "done": break
        time.sleep(0.05)
    
    time.sleep(0.2) # let TTL expire
    jm._cleanup_expired() # Force eviction
    
    assert jm.consultar(job_concluido)["status"] == "not_found"
    assert jm.consultar(job_em_execucao)["status"] == "running"
    
    ev_finish.set()
    jm.shutdown()

def test_11_duas_operacoes_leitura():
    jm = JobManager(watchdog_interval=0.1)
    ev = threading.Event()
    
    def operacao():
        ev.wait()
        return {"ok": True}
        
    job_id1 = jm.submit(operacao, exclusive_group=None)
    job_id2 = jm.submit(operacao, exclusive_group=None)
    
    status1 = jm.consultar(job_id1)
    status2 = jm.consultar(job_id2)
    
    assert status1["status"] == "running"
    assert status2["status"] == "running"
    
    ev.set()
    jm.shutdown()

def test_12_13_14_15_grupos_exclusivos():
    jm = JobManager(watchdog_interval=0.1)
    
    ev = threading.Event()
    ev2 = threading.Event()
    def operacao_lenta():
        ev.set()
        ev2.wait()
        return {"ok": True}
        
    job_id1 = jm.submit(operacao_lenta, exclusive_group="system_mutation")
    ev.wait(2.0) # Ensure it grabbed the lock
    
    job_id2 = jm.submit(operacao_lenta, exclusive_group="system_mutation")
    
    status2 = jm.consultar(job_id2)
    assert status2["status"] == "failed"
    assert status2["resultado"]["codigo"] == "JOB_CONFLICT"
    
    payload_str = json.dumps(status2)
    assert "system_mutation" not in payload_str
    
    ev2.set()
    jm.shutdown()

def test_16_17_cem_jobs_concorrentes():
    jm = JobManager(watchdog_interval=0.1)
    ids = []
    
    ev = threading.Event()
    def blocker():
        ev.wait()
        return {"ok": True}
        
    for _ in range(100):
        ids.append(jm.submit(blocker))
        
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
        
    ev.set()
    jm.shutdown()

def test_progress_sanitization():
    jm = JobManager(watchdog_interval=0.1)
    ev = threading.Event()
    ev2 = threading.Event()
    def operacao(job_context=None):
        ev.set()
        ev2.wait()
        return {"ok": True}
        
    job_id = jm.submit(operacao, pass_job_context=True)
    ev.wait(2.0)
    
    # Normal
    jm.update_progress(job_id, 100, "Concluído")
    payload = jm.consultar(job_id)
    assert payload["progresso"] == 100
    assert payload["mensagem"] == "Concluído"
    
    # Malicious
    class Malicious:
        def __repr__(self): return "Hacked!"
    jm.update_progress(job_id, 50, Malicious())
    payload2 = jm.consultar(job_id)
    assert payload2["mensagem"] == "[Objeto Complexo Omitido]"
    
    ev2.set()
    jm.shutdown()

def test_cancellation_cooperative():
    jm = JobManager(watchdog_interval=0.1)
    ev_start = threading.Event()
    ev_cancel = threading.Event()
    
    def operacao(job_context=None):
        ev_start.set()
        ev_cancel.wait() # wait for cancel signal
        job_context.raise_if_cancelled()
        
    job_id = jm.submit(operacao, pass_job_context=True)
    ev_start.wait(2.0)
    
    jm.cancelar(job_id)
    ev_cancel.set()
    
    for _ in range(20):
        if jm.consultar(job_id)["status"] == "cancelled": break
        time.sleep(0.05)
        
    status = jm.consultar(job_id)
    assert status["status"] == "cancelled"
    assert status["resultado"]["codigo"] == "JOB_CANCELLED"
    jm.shutdown()

def test_timeout():
    jm = JobManager(watchdog_interval=0.1)
    ev_start = threading.Event()
    ev_finish = threading.Event()
    
    def operacao():
        ev_start.set()
        ev_finish.wait()
        return {"ok": True}
        
    job_id = jm.submit(operacao, timeout=0.2)
    ev_start.wait(2.0)
    
    for _ in range(20):
        if jm.consultar(job_id)["status"] == "timed_out": break
        time.sleep(0.1)
        
    status = jm.consultar(job_id)
    assert status["status"] == "timed_out"
    assert status["resultado"]["codigo"] == "JOB_TIMEOUT"
    
    ev_finish.set()
    jm.shutdown()

def test_shutdown_behavior():
    jm = JobManager(watchdog_interval=0.1)
    ev = threading.Event()
    
    def longo(job_context=None):
        ev.wait() # Block forever until test ends
        try:
            job_context.raise_if_cancelled()
        except Exception:
            pass
        return {"ok": True}
        
    j_id = jm.submit(longo, pass_job_context=True)
    
    # Initiate shutdown
    jm.shutdown()
    
    # State should be cancel_requested because worker is still alive (ev is blocking)
    assert jm.consultar(j_id)["status"] == "cancel_requested"
    
    # Post-shutdown submission
    res = jm.submit(lambda: {"ok": True})
    # Since shutdown is True, res is a dict, wait, _create_rejected_job returns the job ID!
    # Ah, in my implementation it returns the rejected job ID.
    assert type(res) is str
    status_new = jm.consultar(res)
    assert status_new["status"] == "failed"
    assert status_new["resultado"]["codigo"] == "JOB_MANAGER_SHUTDOWN"
    
    ev.set() # Release worker
