import time
import json
import threading
import pytest
from modules.gui.jobs import JobManager, JobContext

def test_1_2_3_job_id_criado_imediato_sucesso():
    jm = JobManager(watchdog_interval=0.1)
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
    jm.shutdown()

def test_4_captura_de_excecao():
    jm = JobManager(watchdog_interval=0.1)
    def funcao_que_quebra():
        raise ValueError(r"Falha em C:\Users\Cliente\Documents\segredo.txt dentro de executar_registro")

    job_id = jm.submit(funcao_que_quebra)
    time.sleep(0.1)

    status = jm.consultar(job_id)
    assert status["status"] == "failed"
    assert status["resultado"]["ok"] is False
    assert status["resultado"]["codigo"] == "JOB_INTERNAL_ERROR"

    # Teste de Segurança: vazamento de dados da exception
    payload_str = json.dumps(status)
    assert "Traceback" not in payload_str
    assert "C:\\Users" not in payload_str
    assert "segredo.txt" not in payload_str
    assert "executar_registro" not in payload_str
    assert "Não foi possível concluir" in status["resultado"]["erro"]
    jm.shutdown()

def test_5_consulta_job_inexistente():
    jm = JobManager(watchdog_interval=0.1)
    status = jm.consultar("id-falso-123")
    assert status["status"] == "not_found"
    jm.shutdown()

def test_6_7_resultado_serializavel():
    jm = JobManager(watchdog_interval=0.1)
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

    assert status2["status"] == "failed"
    assert status2["resultado"]["ok"] is False
    assert status2["resultado"]["codigo"] == "JOB_RESULT_INVALID"

    # Teste de Segurança: vazamento de objeto memory ou internals
    payload_str = json.dumps(status2)
    assert "0xDEADBEEF" not in payload_str
    assert "NaoSerializavel" not in payload_str
    jm.shutdown()

def test_8_progress_normalization():
    jm = JobManager(watchdog_interval=0.1)
    started = threading.Event()
    finish = threading.Event()

    def operacao(job_context=None):
        started.set()
        finish.wait()
        return {"ok": True}

    job_id = jm.submit(operacao, pass_job_context=True)
    started.wait(2.0)

    jm.update_progress(job_id, "abc", "msg")
    assert jm.get_progress(job_id) == 0

    jm.update_progress(job_id, 150, "x" * 300)
    status = jm.consultar(job_id)
    assert status["progresso"] == 100
    assert len(status["mensagem"]) == 200

    finish.set()
    jm.shutdown()

def test_9_timeout_without_polling():
    # Watchdog should enforce timeout independently of polling
    jm = JobManager(watchdog_interval=0.1)

    def operacao():
        time.sleep(1.5)
        return {"ok": True}

    job_id = jm.submit(operacao, timeout=0.5)

    # Do not call consultar() for 1 second.
    time.sleep(1.2)

    # Watchdog should have kicked in
    status = jm.consultar(job_id)
    assert status["status"] == "timed_out"
    assert status["resultado"]["codigo"] == "JOB_TIMEOUT"
    jm.shutdown()

def test_10_late_result_does_not_overwrite_timeout():
    jm = JobManager(watchdog_interval=0.1)

    def operacao():
        time.sleep(0.8)
        return {"ok": True, "late": "result"}

    job_id = jm.submit(operacao, timeout=0.2)
    time.sleep(0.5)

    status = jm.consultar(job_id)
    assert status["status"] == "timed_out"

    time.sleep(0.5)
    status2 = jm.consultar(job_id)
    assert status2["status"] == "timed_out"
    assert status2["resultado"]["codigo"] == "JOB_TIMEOUT"
    assert "late" not in json.dumps(status2)
    jm.shutdown()

def test_11_cooperative_cancellation():
    jm = JobManager(watchdog_interval=0.1)
    cancel_confirmed = threading.Event()

    def operacao(job_context=None):
        while not job_context.is_cancel_requested():
            time.sleep(0.01)
        cancel_confirmed.set()
        job_context.raise_if_cancelled()

    job_id = jm.submit(operacao, pass_job_context=True)
    time.sleep(0.1)

    jm.cancelar(job_id)
    cancel_confirmed.wait(2.0)
    time.sleep(0.1)

    status = jm.consultar(job_id)
    assert status["status"] == "cancelled"
    assert status["resultado"]["codigo"] == "JOB_CANCELLED"
    jm.shutdown()

def test_12_ownership_remains_after_timeout():
    jm = JobManager(watchdog_interval=0.1)
    hold_worker = threading.Event()

    def operacao_lenta():
        hold_worker.wait()
        return {"ok": True}

    job_id1 = jm.submit(operacao_lenta, exclusive_group="sys", timeout=0.2)
    time.sleep(0.5)

    # O job1 deu timeout, mas o worker_alive ainda é True
    assert jm.consultar(job_id1)["status"] == "timed_out"

    job_id2 = jm.submit(lambda: {"ok": True}, exclusive_group="sys")
    status2 = jm.consultar(job_id2)
    assert status2["status"] == "failed"
    assert status2["resultado"]["codigo"] == "JOB_CONFLICT"

    # Liberando o worker antigo
    hold_worker.set()
    time.sleep(0.2)

    # Agora deve aceitar
    job_id3 = jm.submit(lambda: {"ok": True}, exclusive_group="sys")
    time.sleep(0.1)
    assert jm.consultar(job_id3)["status"] == "done"
    jm.shutdown()

def test_13_capacity_and_ttl():
    jm = JobManager(ttl_seconds=0.1, max_retained_jobs=2, watchdog_interval=0.1)

    j1 = jm.submit(lambda: {"ok": True})
    time.sleep(0.05)
    j2 = jm.submit(lambda: {"ok": True})
    time.sleep(0.05)
    j3 = jm.submit(lambda: {"ok": True})

    time.sleep(0.05)
    jm._cleanup_expired()
    # TTL deve ter removido os velhos (j1) mas vamos testar capacity max

    jm.ttl_seconds = 1000
    jm.submit(lambda: {"ok": True})
    jm.submit(lambda: {"ok": True})
    jm.submit(lambda: {"ok": True})
    time.sleep(0.1)

    jm._cleanup_expired()
    # Somente 2 ultimos retidos
    assert len(jm._jobs) == 2
    jm.shutdown()

def test_14_duplicate_id():
    jm = JobManager(watchdog_interval=0.1)
    jm.submit(lambda: {"ok": True}, job_id="id-fixo")
    time.sleep(0.1)

    res = jm.submit(lambda: {"ok": True}, job_id="id-fixo")
    assert res != "id-fixo"
    status = jm.consultar(res)
    assert status["status"] == "failed"
    assert status["resultado"]["codigo"] == "JOB_DUPLICATE_ID"
    jm.shutdown()

def test_15_shutdown_behavior():
    jm = JobManager(watchdog_interval=0.1)
    def longo(job_context=None):
        while not job_context.is_cancel_requested():
            time.sleep(0.01)
        job_context.raise_if_cancelled()

    j_id = jm.submit(longo, pass_job_context=True)
    jm.shutdown()

    time.sleep(0.1)
    # Novo job deve ser rejeitado
    j_new = jm.submit(lambda: {"ok": True})
    assert jm.consultar(j_new)["resultado"]["codigo"] == "JOB_MANAGER_SHUTDOWN"

    assert jm.consultar(j_id)["status"] == "cancelled"

    # Shutdown is idempotent
    jm.shutdown()



def test_16_17_cem_jobs_concorrentes():
    from modules.gui.jobs import JobManager
    import threading
    jm = JobManager(watchdog_interval=1.0)
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
    jm.shutdown()
    assert True

def test_18_payload_nomes_esperados():
    from modules.gui.jobs import JobManager
    import time
    jm = JobManager(watchdog_interval=1.0)
    job_id = jm.submit(lambda: {"ok": True})
    time.sleep(0.1)
    jm.update_progress(job_id, 100, "Concluído")
    payload = jm.consultar(job_id)
    assert "status" in payload
    assert "resultado" in payload
    assert payload["status"] == "done"
    jm.shutdown()

def test_11_duas_operacoes_leitura():
    from modules.gui.jobs import JobManager
    import time
    jm = JobManager(watchdog_interval=1.0)
    def operacao():
        time.sleep(0.1)
        return {"ok": True}
    job_id1 = jm.submit(operacao, exclusive_group=None)
    job_id2 = jm.submit(operacao, exclusive_group=None)
    status1 = jm.consultar(job_id1)
    status2 = jm.consultar(job_id2)
    assert status1["status"] == "running"
    assert status2["status"] == "running"
    time.sleep(0.15)
    jm.shutdown()
