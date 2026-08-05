import time
import json
import threading
import pytest
from modules.gui.jobs import JobManager, JobContext
from modules.core.exceptions import JobCancelledError

def wait_for_status(jm, job_id, statuses, timeout=2.0):
    if isinstance(statuses, str):
        statuses = [statuses]
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        status = jm.consultar(job_id)
        if status["status"] in statuses:
            return status
        time.sleep(0.01)
    raise TimeoutError(f"Job {job_id} never reached statuses: {statuses}")

def wait_for_worker_exit(jm, job_id, timeout=2.0):
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        with jm._lock:
            job = jm._jobs.get(job_id)
            if not job or not job["worker_alive"]:
                return
        time.sleep(0.01)
    raise TimeoutError(f"Worker for {job_id} never exited")

def test_1_2_3_job_id_criado_imediato_sucesso():
    jm = JobManager(watchdog_interval=0.1)
    ev_started = threading.Event()
    ev_can_finish = threading.Event()

    def acao():
        ev_started.set()
        ev_can_finish.wait(5.0)
        return {"ok": True, "dado": 42}

    job_id = jm.submit(acao)
    assert type(job_id) is str

    ev_started.wait(2.0)
    ev_can_finish.set()

    status = wait_for_status(jm, job_id, "done")
    assert status["resultado"]["ok"] is True
    assert status["resultado"]["dado"] == 42

    wait_for_worker_exit(jm, job_id)
    jm.shutdown()

def test_4_captura_de_excecao():
    jm = JobManager(watchdog_interval=0.1)
    ev_started = threading.Event()

    def funcao_que_quebra():
        ev_started.set()
        raise ValueError(r"Falha em C:\Users\Cliente\Documents\segredo.txt dentro de executar_registro")

    job_id = jm.submit(funcao_que_quebra)
    ev_started.wait(2.0)

    status = wait_for_status(jm, job_id, "failed")
    assert status["resultado"]["ok"] is False
    assert status["resultado"]["codigo"] == "JOB_INTERNAL_ERROR"

    payload_str = json.dumps(status)
    assert "Traceback" not in payload_str
    assert "C:\\Users" not in payload_str
    assert "segredo.txt" not in payload_str
    assert "executar_registro" not in payload_str

    wait_for_worker_exit(jm, job_id)
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

    status = wait_for_status(jm, job_id, "done")
    assert "lista" in json.dumps(status)
    wait_for_worker_exit(jm, job_id)

    class NaoSerializavel:
        def __repr__(self): return "<NaoSerializavel memory_addr: 0xDEADBEEF>"

    ev2 = threading.Event()
    def broken():
        ev2.set()
        return {"ok": True, "objeto": NaoSerializavel()}

    job_id2 = jm.submit(broken)
    ev2.wait(2.0)

    status2 = wait_for_status(jm, job_id2, "failed")
    assert status2["resultado"]["codigo"] == "JOB_RESULT_INVALID"
    payload_str = json.dumps(status2)
    assert "0xDEADBEEF" not in payload_str
    assert "NaoSerializavel" not in payload_str
    wait_for_worker_exit(jm, job_id2)

    d = {}
    d["loop"] = d
    ev3 = threading.Event()
    def broken_circular():
        ev3.set()
        return {"ok": True, "circular": d}

    job_id3 = jm.submit(broken_circular)
    ev3.wait(2.0)

    status3 = wait_for_status(jm, job_id3, "failed")
    assert status3["resultado"]["codigo"] == "JOB_RESULT_INVALID"
    wait_for_worker_exit(jm, job_id3)

    jm.shutdown()

def test_8_9_ttl_remove_job():
    jm = JobManager(ttl_seconds=0.1, max_retained_jobs=10, watchdog_interval=0.1)
    ev_start = threading.Event()
    ev_finish = threading.Event()

    def job_lento():
        ev_start.set()
        ev_finish.wait(5.0)
        return {"ok": True}

    ev2 = threading.Event()
    def rapido():
        ev2.set()
        return {"ok": True}

    job_em_execucao = jm.submit(job_lento)
    job_concluido = jm.submit(rapido)

    ev_start.wait(2.0)
    ev2.wait(2.0)

    wait_for_status(jm, job_concluido, "done")
    wait_for_worker_exit(jm, job_concluido)

    # Patch time instead of sleeping
    import unittest.mock
    with unittest.mock.patch('time.time', return_value=time.time() + 10.0):
        jm._cleanup_expired()

    assert jm.consultar(job_concluido)["status"] == "not_found"
    assert jm.consultar(job_em_execucao)["status"] == "running"

    ev_finish.set()
    wait_for_worker_exit(jm, job_em_execucao)
    jm.shutdown()

def test_11_duas_operacoes_leitura():
    jm = JobManager(watchdog_interval=0.1)
    ev = threading.Event()

    def operacao():
        ev.wait(5.0)
        return {"ok": True}

    job_id1 = jm.submit(operacao, exclusive_group=None)
    job_id2 = jm.submit(operacao, exclusive_group=None)

    status1 = jm.consultar(job_id1)
    status2 = jm.consultar(job_id2)
    assert status1["status"] == "running"
    assert status2["status"] == "running"

    ev.set()
    wait_for_worker_exit(jm, job_id1)
    wait_for_worker_exit(jm, job_id2)
    jm.shutdown()

def test_12_13_14_15_grupos_exclusivos():
    jm = JobManager(watchdog_interval=0.1)
    ev = threading.Event()
    ev2 = threading.Event()

    def operacao_lenta():
        ev.set()
        ev2.wait(5.0)
        return {"ok": True}

    job_id1 = jm.submit(operacao_lenta, exclusive_group="system_mutation")
    ev.wait(2.0)

    job_id2 = jm.submit(operacao_lenta, exclusive_group="system_mutation")
    status2 = jm.consultar(job_id2)
    assert status2["status"] == "failed"
    assert status2["resultado"]["codigo"] == "JOB_CONFLICT"

    payload_str = json.dumps(status2)
    assert "system_mutation" not in payload_str

    ev2.set()
    wait_for_worker_exit(jm, job_id1)
    jm.shutdown()

def test_16_17_cem_jobs_concorrentes():
    jm = JobManager(watchdog_interval=0.1)
    ids = []
    ev = threading.Event()

    def blocker():
        ev.wait(5.0)
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
        t.join(timeout=2.0)

    ev.set()
    for i in ids:
        wait_for_worker_exit(jm, i)
    jm.shutdown()

def test_progress_sanitization():
    jm = JobManager(watchdog_interval=0.1)
    ev = threading.Event()
    ev2 = threading.Event()

    def operacao(job_context=None):
        ev.set()
        ev2.wait(5.0)
        return {"ok": True}

    job_id = jm.submit(operacao, pass_job_context=True)
    ev.wait(2.0)

    jm.update_progress(job_id, 100, "Concluído")
    payload = jm.consultar(job_id)
    assert payload["progresso"] == 100
    assert payload["mensagem"] == "Concluído"

    class Malicious:
        def __repr__(self): return "Hacked!"
    jm.update_progress(job_id, 50, Malicious())
    payload2 = jm.consultar(job_id)
    assert payload2["mensagem"] == "[Objeto Complexo Omitido]"

    ev2.set()
    wait_for_worker_exit(jm, job_id)
    jm.shutdown()

def test_cancellation_cooperative():
    jm = JobManager(watchdog_interval=0.1)
    ev_start = threading.Event()
    ev_cancel = threading.Event()

    def operacao(job_context=None):
        ev_start.set()
        ev_cancel.wait(5.0)
        job_context.raise_if_cancelled()

    job_id = jm.submit(operacao, pass_job_context=True)
    ev_start.wait(2.0)

    jm.cancelar(job_id)
    ev_cancel.set()

    status = wait_for_status(jm, job_id, "cancelled")
    assert status["resultado"]["codigo"] == "JOB_CANCELLED"
    wait_for_worker_exit(jm, job_id)
    jm.shutdown()

def test_timeout():
    jm = JobManager(watchdog_interval=0.1)
    ev_start = threading.Event()
    ev_finish = threading.Event()

    def operacao():
        ev_start.set()
        ev_finish.wait(5.0)
        return {"ok": True}

    job_id = jm.submit(operacao, timeout=0.2)
    ev_start.wait(2.0)

    status = wait_for_status(jm, job_id, "timed_out")
    assert status["resultado"]["codigo"] == "JOB_TIMEOUT"

    ev_finish.set()
    wait_for_worker_exit(jm, job_id)

    status_after = jm.consultar(job_id)
    assert status_after["status"] == "timed_out"
    jm.shutdown()

def test_shutdown_behavior_non_cooperative_success():
    jm = JobManager(watchdog_interval=0.1)
    ev_started = threading.Event()
    ev_can_finish = threading.Event()

    def longo(job_context=None):
        ev_started.set()
        ev_can_finish.wait(5.0)
        return {"ok": True, "dado": "real_result"}

    j_id = jm.submit(longo, pass_job_context=True, exclusive_group="system_mutation")
    ev_started.wait(2.0)

    jm.shutdown()

    status = jm.consultar(j_id)
    assert status["status"] == "cancel_requested"

    # Another mutation rejected
    res = jm.submit(lambda: {"ok": True}, exclusive_group="system_mutation")
    assert type(res) is str
    status_new = jm.consultar(res)
    assert status_new["status"] == "failed"
    assert status_new["resultado"]["codigo"] == "JOB_MANAGER_SHUTDOWN"

    ev_can_finish.set()
    wait_for_worker_exit(jm, j_id)

    # Must be done, not cancelled, and retain its real result
    status_final = jm.consultar(j_id)
    assert status_final["status"] == "done"
    assert status_final["resultado"]["ok"] is True
    assert status_final["resultado"]["dado"] == "real_result"

    assert "system_mutation" not in jm._exclusive_groups

    jm._watchdog.join(timeout=2.0)
    assert not jm._watchdog.is_alive()

def test_shutdown_behavior_non_cooperative_failure():
    jm = JobManager(watchdog_interval=0.1)
    ev_started = threading.Event()
    ev_can_finish = threading.Event()

    def falho(job_context=None):
        ev_started.set()
        ev_can_finish.wait(5.0)
        raise RuntimeError("Non-cooperative failure")

    j_id = jm.submit(falho, pass_job_context=True)
    ev_started.wait(2.0)

    jm.cancelar(j_id)
    status = jm.consultar(j_id)
    assert status["status"] == "cancel_requested"

    ev_can_finish.set()
    wait_for_worker_exit(jm, j_id)

    # Must be failed, not cancelled
    status_final = jm.consultar(j_id)
    assert status_final["status"] == "failed"
    assert status_final["resultado"]["codigo"] == "JOB_INTERNAL_ERROR"

    jm.shutdown()

def test_shutdown_behavior_duplicate_id_protection():
    jm = JobManager(watchdog_interval=0.1)
    ev_started = threading.Event()
    ev_can_finish = threading.Event()

    def longo(job_context=None):
        ev_started.set()
        ev_can_finish.wait(5.0)
        return {"ok": True, "dado": "real_result"}

    # 1. Submit an exclusive worker using job_id="fixed-active-id"
    j_id = jm.submit(longo, job_id="fixed-active-id", pass_job_context=True, exclusive_group="system_mutation")
    assert j_id == "fixed-active-id"

    # 2. Confirm it started
    ev_started.wait(2.0)

    # 3. Call shutdown()
    jm.shutdown()

    # 4. Submit again using the same job_id
    res = jm.submit(lambda: {"ok": True}, job_id="fixed-active-id", exclusive_group="system_mutation")

    # 5. Confirm the returned rejection ID is different
    assert res != "fixed-active-id"
    assert type(res) is str

    # 6. Confirm the original record still exists and is cancel_requested
    status = jm.consultar("fixed-active-id")
    assert status["status"] == "cancel_requested"

    # 7. Confirm the original worker still owns the exclusive group
    assert jm._exclusive_groups.get("system_mutation") == "fixed-active-id"

    # 8. Release the original worker
    ev_can_finish.set()
    wait_for_worker_exit(jm, "fixed-active-id")

    # 9. Confirm its real final result remains intact
    status_final = jm.consultar("fixed-active-id")
    assert status_final["status"] == "done"
    assert status_final["resultado"]["dado"] == "real_result"

    # 10. Confirm ownership is released only after its actual exit
    assert "system_mutation" not in jm._exclusive_groups

    jm.shutdown()

def test_callback_exactly_once():
    cb_calls = []
    def terminal_cb(job_id, job):
        cb_calls.append((job_id, job["status"]))
        
    jm = JobManager(watchdog_interval=0.1, on_terminal_state=terminal_cb)
    ev_start = threading.Event()
    ev_finish = threading.Event()

    def operacao():
        ev_start.set()
        ev_finish.wait(5.0)
        return {"ok": True}

    job_id = jm.submit(operacao, timeout=0.2)
    ev_start.wait(2.0)
    
    # Check that it timed out and callback called
    wait_for_status(jm, job_id, "timed_out")
    
    # Now let the worker exit
    ev_finish.set()
    wait_for_worker_exit(jm, job_id)
    
    # Callback should be called exactly once
    assert len(cb_calls) == 1
    assert cb_calls[0][1] == "timed_out"
    jm.shutdown()

def test_recursive_sanitization():
    jm = JobManager(watchdog_interval=0.1)
    ev_start = threading.Event()
    ev_finish = threading.Event()

    def operacao(job_context=None):
        ev_start.set()
        
        nested_dict = {}
        curr = nested_dict
        for i in range(10):
            curr["level"] = {}
            curr = curr["level"]
            
        job_context.update_progress(50, "deep", nested_dict)
        ev_finish.wait(5.0)
        return {"ok": True}

    job_id = jm.submit(operacao, pass_job_context=True)
    ev_start.wait(2.0)
    
    payload = jm.consultar(job_id)
    snapshot = payload.get("detalhes_progresso")
    
    # It should not have 10 levels because max depth is 5
    curr = snapshot
    levels = 0
    while isinstance(curr, dict) and "level" in curr:
        levels += 1
        curr = curr["level"]
    
    assert levels <= 6
    
    ev_finish.set()
    wait_for_worker_exit(jm, job_id)
    jm.shutdown()

def test_recursive_serialization_error_and_finalization():
    import sys
    ev_start = threading.Event()

    cb_calls = []
    def term_cb(job_id, job):
        cb_calls.append((job_id, job["status"], job["resultado"]))

    jm = JobManager(watchdog_interval=0.1, on_terminal_state=term_cb)

    def operacao():
        ev_start.set()
        d = {}
        curr = d
        for i in range(sys.getrecursionlimit() + 5000):
            curr["a"] = {}
            curr = curr["a"]
        return d

    job_id = jm.submit(operacao, exclusive_group="test_group")
    
    # The group may have been cleared if the thread ran too fast, so skip checking it here.
    ev_start.wait(2.0)
    wait_for_worker_exit(jm, job_id)
    
    status = jm.consultar(job_id)
    assert status["status"] == "failed"
    assert status["resultado"]["codigo"] == "JOB_RESULT_INVALID"
    
    with jm._lock:
        job_internal = jm._jobs[job_id]
        assert job_internal["worker_alive"] is False
        assert job_internal["completed_at"] is not None
    
    assert len(cb_calls) == 1
    assert cb_calls[0][1] == "failed"
    assert cb_calls[0][2]["codigo"] == "JOB_RESULT_INVALID"
    
    assert jm._exclusive_groups.get("test_group") is None
    jm.shutdown()

def test_json_dumps_unexpected_error():
    ev_start = threading.Event()

    cb_calls = []
    def term_cb(job_id, job):
        cb_calls.append((job_id, job["status"], job["resultado"]))

    jm = JobManager(watchdog_interval=0.1, on_terminal_state=term_cb)

    class UnserializableObject:
        pass

    def operacao():
        ev_start.set()
        return UnserializableObject()

    job_id = jm.submit(operacao, exclusive_group="test_group_2")
    ev_start.wait(2.0)
    
    wait_for_worker_exit(jm, job_id)
    
    status = jm.consultar(job_id)
    assert status["status"] == "failed"
    assert status["resultado"]["codigo"] == "JOB_RESULT_INVALID"
    
    with jm._lock:
        job_internal = jm._jobs[job_id]
        assert job_internal["worker_alive"] is False
        assert job_internal["completed_at"] is not None
    
    assert len(cb_calls) == 1
    assert cb_calls[0][1] == "failed"
    
    assert jm._exclusive_groups.get("test_group_2") is None
    jm.shutdown()
