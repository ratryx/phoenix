import pytest
from modules.core.routine_service import RoutineService
from modules.core.exceptions import JobCancelledError
import logging
import threading
import time
from modules.gui.jobs import JobManager

class FakeDiagnostico:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.calls = 0
    def coletar_diagnostico_silencioso(self):
        self.calls += 1
        if self.fail_on == "initial_diag" and self.calls == 1:
            raise RuntimeError("Sensitive failure initial diag C:\\Users\\Client\\secret.txt")
        if self.fail_on == "final_diag" and self.calls == 2:
            raise RuntimeError("Sensitive failure final diag C:\\Users\\Client\\secret.txt")
        return {"status": "ok_diag"}

class FakeLimpeza:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.calls = 0
    def executar_limpeza(self, progress_callback=None, cancel_event=None, incluir_lixeira=False):
        self.calls += 1
        if self.fail_on == "cleanup":
            raise RuntimeError("Sensitive failure cleanup C:\\Users\\Client\\secret.txt")
        return {"espaco_liberado_mb": 500.0, "arquivos_removidos": 100, "arquivos_ignorados": 0}

class FakeOtimizacao:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.calls = 0
    def executar_otimizacao_geral(self, id_atendimento, cancel_event=None):
        self.calls += 1
        if cancel_event and cancel_event.is_set():
            return {"ok": False, "codigo": "COMMAND_CANCELLED"}
        if self.fail_on == "optimization":
            raise RuntimeError("Sensitive failure optimization C:\\Users\\Client\\secret.txt")
        return {"ok": True, "codigo": "COMMAND_OK"}

class FakeLogs:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.snapshots = {}
        self.acoes = []
        self.save_calls = 0
        self.load_calls = 0
    def salvar_snapshot(self, id_atendimento, etapa, dados, nome_cliente):
        self.save_calls += 1
        if self.fail_on == "initial_snapshot_persistence" and etapa == "antes":
            raise RuntimeError("Sensitive failure snapshot antes C:\\Users\\Client\\secret.txt")
        if self.fail_on == "final_snapshot_persistence" and etapa == "depois":
            raise RuntimeError("Sensitive failure snapshot depois C:\\Users\\Client\\secret.txt")
        if id_atendimento not in self.snapshots:
            self.snapshots[id_atendimento] = {}
        self.snapshots[id_atendimento][etapa] = dados
    def registrar_acao(self, id_atendimento, acao, detalhe="", nome_cliente=""):
        self.acoes.append((id_atendimento, acao))
    def obter_pasta_logs(self):
        import pathlib
        return pathlib.Path("/tmp/fake_logs")
    def carregar_snapshot(self, id_atendimento, etapa):
        self.load_calls += 1
        if self.fail_on == "snapshot_loading":
            raise RuntimeError("Sensitive failure load snapshot C:\\Users\\Client\\secret.txt")
        return self.snapshots.get(id_atendimento, {}).get(etapa)

class FakeRelatorio:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.exportacoes = []
    def exportar_relatorio_txt(self, antes, depois, liberado, caminho):
        if self.fail_on == "text-report_export":
            raise RuntimeError("Sensitive failure report export C:\\Users\\Client\\secret.txt")
        self.exportacoes.append((antes, depois, liberado, caminho))

def test_routine_service_sucesso():
    f_diag = FakeDiagnostico()
    f_limp = FakeLimpeza()
    f_otim = FakeOtimizacao()
    f_logs = FakeLogs()
    f_rel = FakeRelatorio()

    service = RoutineService(
        diagnostico_module=f_diag,
        cleanup_service_module=f_limp,
        otimizacao_module=f_otim,
        logs_module=f_logs,
        relatorio_module=f_rel
    )

    res = service.executar(id_atendimento="123", nome_cliente="TestClient")

    assert res["ok"] is True
    assert res["id_atendimento"] == "123"
    assert res["espaco_liberado_mb"] == 500.0
    assert "123_relatorio.txt" in res["relatorio_txt"]

    assert len(f_logs.acoes) == 4 # 2 diags + 1 limpeza + 1 conclusão
    assert f_logs.acoes[0] == ("123", "Diagnóstico inicial coletado")
    assert f_logs.acoes[1] == ("123", "Limpeza executada")
    assert f_logs.acoes[2] == ("123", "Diagnóstico final coletado")
    assert f_logs.acoes[3] == ("123", "Rotina concluída com sucesso")


def test_routine_service_validacao_id():
    service = RoutineService(FakeDiagnostico(), FakeLimpeza(), FakeOtimizacao(), FakeLogs(), FakeRelatorio())
    with pytest.raises(ValueError, match="obrigatório"):
        service.executar(id_atendimento=None)
    with pytest.raises(ValueError, match="obrigatório"):
        service.executar(id_atendimento="")

@pytest.mark.parametrize("phase", [
    "initial_diag",
    "initial_snapshot_persistence",
    "cleanup",
    "optimization",
    "final_diag",
    "final_snapshot_persistence",
    "snapshot_loading",
    "text-report_export"
])
def test_routine_service_falha_sanitizada(phase):
    f_diag = FakeDiagnostico(fail_on=phase)
    f_limp = FakeLimpeza(fail_on=phase)
    f_otim = FakeOtimizacao(fail_on=phase)
    f_logs = FakeLogs(fail_on=phase)
    f_rel = FakeRelatorio(fail_on=phase)
    service = RoutineService(f_diag, f_limp, f_otim, f_logs, f_rel)

    res = service.executar("123")
    assert res["ok"] is False
    assert res["codigo"] == "ROUTINE_FAILED"
    assert res["erro"] == "Não foi possível concluir a rotina."

    res_str = str(res)
    assert "secret.txt" not in res_str
    assert "Sensitive failure" not in res_str

    acao_falha = [a for id_, a in f_logs.acoes if "Falha durante a execução" in a]
    assert len(acao_falha) == 1
    acao = acao_falha[0]
    assert "secret.txt" not in acao
    assert "Sensitive failure" not in acao

    assert len(f_rel.exportacoes) == 0

class FakeJobContext:
    def __init__(self, cancel_after_phase=0):
        self.phase = 0
        self.cancel_after_phase = cancel_after_phase
        import threading
        self.cancel_event = threading.Event()
    def is_cancel_requested(self):
        return self.phase >= self.cancel_after_phase
    def raise_if_cancelled(self):
        self.phase += 1
        if self.phase >= self.cancel_after_phase:
            self.cancel_event.set()
            raise JobCancelledError("Job cancelled cooperatively")
    def update_progress(self, pct, msg):
        pass

@pytest.mark.parametrize("cp", range(1, 10))
def test_routine_service_cancellation_checkpoints(cp):
    f_diag = FakeDiagnostico()
    f_limp = FakeLimpeza()
    f_otim = FakeOtimizacao()
    f_logs = FakeLogs()
    f_rel = FakeRelatorio()
    service = RoutineService(f_diag, f_limp, f_otim, f_logs, f_rel)

    with pytest.raises(JobCancelledError):
        service.executar("123", job_context=FakeJobContext(cancel_after_phase=cp))

    acao_cancel = [a for id_, a in f_logs.acoes if "Rotina cancelada pelo usuário" in a]
    assert len(acao_cancel) == 1

    assert len(f_rel.exportacoes) == 0

def test_integration_routine_cancellation():
    # Submit the real routine service via JobManager
    # and verify it yields status=cancelled and codigo=JOB_CANCELLED
    jm = JobManager(watchdog_interval=0.1)

    f_diag = FakeDiagnostico()
    f_limp = FakeLimpeza()
    f_otim = FakeOtimizacao()
    f_logs = FakeLogs()
    f_rel = FakeRelatorio()
    service = RoutineService(f_diag, f_limp, f_otim, f_logs, f_rel)

    ev_wait = threading.Event()

    # We override executing routine to block so we can cancel it
    original_exec = service.executar
    def proxy_executar(*args, **kwargs):
        ev_wait.wait(2.0)
        job_context = kwargs.get("job_context")
        if job_context:
            job_context.raise_if_cancelled()
        return original_exec(*args, **kwargs)

    service.executar = proxy_executar

    def target_fn(ctx):
        return service.executar("123", job_context=ctx)

    job_id = jm.submit(target_fn, pass_job_context=True)

    # wait a moment to make sure it started waiting on ev_wait
    time.sleep(0.1)

    # Cancel it
    jm.cancelar(job_id)
    ev_wait.set()

    # wait for it to finish
    start = time.monotonic()
    while time.monotonic() - start < 2.0:
        st = jm.consultar(job_id)
        if st["status"] == "cancelled":
            break
        time.sleep(0.01)

    st = jm.consultar(job_id)
    assert st["status"] == "cancelled"
    assert st["resultado"]["codigo"] == "JOB_CANCELLED"

    jm.shutdown()
