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

    # Validar retorno e contrato real (chaves exatas, tipos)
    assert "ok" in res and res["ok"] is True
    assert "id_atendimento" in res and res["id_atendimento"] == "123"
    assert "espaco_liberado_mb" in res and res["espaco_liberado_mb"] == 500.0
    assert "relatorio_txt" in res and "123_relatorio.txt" in res["relatorio_txt"]
    assert "antes" in res and res["antes"] == {"status": "ok_diag"}
    assert "depois" in res and res["depois"] == {"status": "ok_diag"}
    
    assert len(res.keys()) == 6

    # Validar side-effects na ordem certa
    assert len(f_logs.acoes) == 2
    assert f_logs.acoes[0] == ("123", "Diagnóstico inicial coletado")
    assert f_logs.acoes[1] == ("123", "Diagnóstico final coletado")
    assert f_logs.snapshots["123"]["antes"] == {"status": "ok_diag"}
    assert f_logs.snapshots["123"]["depois"] == {"status": "ok_diag"}

    assert len(f_rel.exportacoes) == 1
    assert f_rel.exportacoes[0][0] == {"status": "ok_diag"} # antes
    assert f_rel.exportacoes[0][1] == {"status": "ok_diag"} # depois
    assert f_rel.exportacoes[0][2] == 500.0 # mb


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


# ---------------- Falhas Estruturais ----------------

def test_routine_service_falha_diagnostico_inicial(caplog):
    class DiagFalha:
        def coletar_diagnostico_silencioso(self):
            raise RuntimeError("Erro no diag inicial")
            
    service = RoutineService(DiagFalha(), FakeLimpeza(), FakeOtimizacao(), FakeLogs(), FakeRelatorio())
    
    # A rotina aborta propagando a exceção (será pega pelo JobManager que não vaza traceback pro frontend)
    with pytest.raises(RuntimeError, match="Erro no diag inicial"):
        service.executar("123")

def test_routine_service_falha_limpeza():
    class LimpFalha:
        def executar_limpeza_completa(self, id_atendimento):
            raise PermissionError("Acesso negado disco")
            
    f_logs = FakeLogs()
    service = RoutineService(FakeDiagnostico(), LimpFalha(), FakeOtimizacao(), f_logs, FakeRelatorio())
    
    with pytest.raises(PermissionError, match="Acesso negado"):
        service.executar("123")
        
    # Validar que parou na limpeza
    assert len(f_logs.acoes) == 1
    assert f_logs.acoes[0] == ("123", "Diagnóstico inicial coletado")

def test_routine_service_falha_otimizacao():
    class OtimFalha:
        def executar_otimizacao_geral(self, id_atendimento):
            raise OSError("Registro inacessivel")
            
    f_logs = FakeLogs()
    service = RoutineService(FakeDiagnostico(), FakeLimpeza(), OtimFalha(), f_logs, FakeRelatorio())
    
    with pytest.raises(OSError, match="Registro"):
        service.executar("123")

def test_routine_service_falha_diagnostico_final():
    class DiagParcial:
        def __init__(self):
            self.chamadas = 0
        def coletar_diagnostico_silencioso(self):
            self.chamadas += 1
            if self.chamadas == 1:
                return {"status": "ok_diag"}
            raise RuntimeError("Falha no segundo diag")
            
    f_logs = FakeLogs()
    service = RoutineService(DiagParcial(), FakeLimpeza(), FakeOtimizacao(), f_logs, FakeRelatorio())
    
    with pytest.raises(RuntimeError, match="Falha no segundo"):
        service.executar("123")
        
    assert len(f_logs.acoes) == 1

def test_routine_service_falha_salvar_atendimento():
    class LogsFalha(FakeLogs):
        def salvar_snapshot(self, *args, **kwargs):
            raise IOError("Sem espaco disco")
            
    service = RoutineService(FakeDiagnostico(), FakeLimpeza(), FakeOtimizacao(), LogsFalha(), FakeRelatorio())
    
    with pytest.raises(IOError, match="Sem espaco"):
        service.executar("123")

def test_routine_service_falha_relatorio():
    class RelatorioFalha(FakeRelatorio):
        def exportar_relatorio_txt(self, *args, **kwargs):
            raise ValueError("Erro ao montar TXT")
            
    f_logs = FakeLogs()
    service = RoutineService(FakeDiagnostico(), FakeLimpeza(), FakeOtimizacao(), f_logs, RelatorioFalha())
    
    with pytest.raises(ValueError, match="Erro ao montar TXT"):
        service.executar("123")
        
    # Deve ter chegado ate o final (diagnostico final ok) mas quebrou antes de retornar payload
    assert len(f_logs.acoes) == 2
