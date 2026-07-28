import pytest
from modules.core.routine_service import RoutineService
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
    def ativar_plano_energia_alto_desempenho(self):
        pass
    def ativar_modo_jogo_windows(self):
        pass
    def desativar_gamebar_overlay(self):
        pass
    def otimizar_gpu_para_jogos(self):
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
    def gerar_pdf(self, id_atendimento, nome_cliente, diag_inicial, diag_final, bytes_liberados):
        return "123_relatorio.pdf"

def test_routine_service_sucesso():
    service = RoutineService(FakeDiagnostico(), FakeLimpeza(), FakeOtimizacao(), FakeLogs(), FakeRelatorio())
    res = service.executar(id_atendimento="123", nome_cliente="TestClient")
    assert "ok" in res and res["ok"] is True
    assert res["espaco_liberado_mb"] == 500.0
    assert "relatorio_gerado" in res

def test_routine_service_falha_diagnostico_inicial():
    class DiagFalha:
        def coletar_diagnostico_silencioso(self):
            raise RuntimeError("Erro no diag inicial")
    service = RoutineService(DiagFalha(), FakeLimpeza(), FakeOtimizacao(), FakeLogs(), FakeRelatorio())
    res = service.executar("123", "Cliente Teste")
    assert res["ok"] is False
    assert "Erro no diag inicial" in res["erro"]

def test_routine_service_falha_limpeza():
    class LimpFalha:
        def executar_limpeza_completa(self, id_atendimento):
            raise PermissionError("Acesso negado disco")
    service = RoutineService(FakeDiagnostico(), LimpFalha(), FakeOtimizacao(), FakeLogs(), FakeRelatorio())
    res = service.executar("123", "Cliente Teste")
    assert res["ok"] is False
    assert "Acesso negado" in res["erro"]

class FakeJobContext:
    def __init__(self, cancel_after_phase=0):
        self.phase = 0
        self.cancel_after_phase = cancel_after_phase
    def is_cancel_requested(self):
        self.phase += 1
        return self.phase >= self.cancel_after_phase
    def raise_if_cancelled(self):
        if self.is_cancel_requested():
            raise Exception("Job cancelled cooperatively")
    def update_progress(self, pct, msg):
        pass

def test_routine_service_cancellation_checkpoints():
    # Cancel at the beginning
    service = RoutineService(FakeDiagnostico(), FakeLimpeza(), FakeOtimizacao(), FakeLogs(), FakeRelatorio())
    res1 = service.executar("123", "Cliente", job_context=FakeJobContext(cancel_after_phase=1))
    assert res1["ok"] is False
    assert res1["codigo"] == "JOB_CANCELLED"

    # Cancel after initial diag
    res2 = service.executar("123", "Cliente", job_context=FakeJobContext(cancel_after_phase=3)) # Initial diag calls it twice (before and after)
    assert res2["ok"] is False
    assert res2["codigo"] == "JOB_CANCELLED"
