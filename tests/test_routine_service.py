import pytest
from modules.core.routine_service import RoutineService
from modules.core.exceptions import JobCancelledError
import logging

class FakeDiagnostico:
    def coletar_diagnostico_silencioso(self):
        return {"status": "ok_diag"}

class FakeLimpeza:
    def executar_limpeza_completa(self, id_atendimento):
        return 1024 * 1024 * 500  # 500 MB

class FakeOtimizacao:
    def executar_otimizacao_geral(self, id_atendimento):
        pass

class FakeLogs:
    def __init__(self):
        self.snapshots = {}
        self.acoes = []
    def salvar_snapshot(self, id_atendimento, etapa, dados, nome_cliente):
        if id_atendimento not in self.snapshots:
            self.snapshots[id_atendimento] = {}
        self.snapshots[id_atendimento][etapa] = dados
    def registrar_acao(self, id_atendimento, acao, nome_cliente=""):
        self.acoes.append((id_atendimento, acao))
    def obter_pasta_logs(self):
        import pathlib
        return pathlib.Path("/tmp/fake_logs")
    def carregar_snapshot(self, id_atendimento, etapa):
        return self.snapshots.get(id_atendimento, {}).get(etapa)

class FakeRelatorio:
    def __init__(self):
        self.exportacoes = []
    def exportar_relatorio_txt(self, antes, depois, liberado, caminho):
        self.exportacoes.append((antes, depois, liberado, caminho))

def test_routine_service_sucesso():
    f_diag = FakeDiagnostico()
    f_limp = FakeLimpeza()
    f_otim = FakeOtimizacao()
    f_logs = FakeLogs()
    f_rel = FakeRelatorio()

    service = RoutineService(
        diagnostico_module=f_diag,
        limpeza_module=f_limp,
        otimizacao_module=f_otim,
        logs_module=f_logs,
        relatorio_module=f_rel
    )

    res = service.executar(id_atendimento="123", nome_cliente="TestClient")

    assert res["ok"] is True
    assert res["id_atendimento"] == "123"
    assert res["espaco_liberado_mb"] == 500.0
    assert "123_relatorio.txt" in res["relatorio_txt"]
    
    assert len(f_logs.acoes) == 3 # 2 diags + 1 conclusão
    assert f_logs.acoes[0] == ("123", "Diagnóstico inicial coletado")
    assert f_logs.acoes[1] == ("123", "Diagnóstico final coletado")
    assert f_logs.acoes[2] == ("123", "Rotina concluída com sucesso")


def test_routine_service_validacao_id():
    service = RoutineService(
        diagnostico_module=FakeDiagnostico(),
        limpeza_module=FakeLimpeza(),
        otimizacao_module=FakeOtimizacao(),
        logs_module=FakeLogs(),
        relatorio_module=FakeRelatorio()
    )
    with pytest.raises(ValueError, match="obrigatório"):
        service.executar(id_atendimento=None)
    with pytest.raises(ValueError, match="obrigatório"):
        service.executar(id_atendimento="")

def test_routine_service_falha_sanitizada():
    class DiagFalha:
        def coletar_diagnostico_silencioso(self):
            raise RuntimeError("Erro no diag inicial vazado")
            
    f_logs = FakeLogs()
    service = RoutineService(DiagFalha(), FakeLimpeza(), FakeOtimizacao(), f_logs, FakeRelatorio())
    
    res = service.executar("123")
    assert res["ok"] is False
    assert res["codigo"] == "ROUTINE_FAILED"
    assert "vazado" not in res["erro"]
    assert len(f_logs.acoes) == 1
    assert "Erro na rotina: Erro no diag inicial vazado" in f_logs.acoes[0][1]

class FakeJobContext:
    def __init__(self, cancel_after_phase=0):
        self.phase = 0
        self.cancel_after_phase = cancel_after_phase
    def is_cancel_requested(self):
        return False
    def raise_if_cancelled(self):
        self.phase += 1
        if self.phase >= self.cancel_after_phase:
            raise JobCancelledError("Job cancelled cooperatively")
    def update_progress(self, pct, msg):
        pass

def test_routine_service_cancellation_checkpoints():
    service = RoutineService(FakeDiagnostico(), FakeLimpeza(), FakeOtimizacao(), FakeLogs(), FakeRelatorio())
    
    # Cancel at checkpoint 1 (before initial diag)
    res1 = service.executar("123", job_context=FakeJobContext(cancel_after_phase=1))
    assert res1["ok"] is False
    assert res1["codigo"] == "JOB_CANCELLED"

    # Cancel at checkpoint 5 (before optimization)
    res5 = service.executar("123", job_context=FakeJobContext(cancel_after_phase=5))
    assert res5["ok"] is False
    assert res5["codigo"] == "JOB_CANCELLED"
