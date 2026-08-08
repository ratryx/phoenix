import pytest
from unittest.mock import MagicMock, patch
from modules.gui.api import PhoenixAPI
from modules.core.exceptions import ProtectionError

@pytest.fixture
def api():
    hw_info = {"status": "carregado"}
    job_manager = MagicMock()
    job_manager.submit.return_value = "job-123"
    api_instance = PhoenixAPI(hw_info=hw_info, job_manager=job_manager)
    return api_instance

# Emulate JobManager submit to run synchronously
def _run_sync(api_instance, method_name, *args, **kwargs):
    worker_captured = []
    def fake_iniciar_job(worker, *a, **kw):
        worker_captured.append(worker)
        return {"job_id": "fake"}
    
    with patch.object(api_instance, '_iniciar_job', side_effect=fake_iniciar_job):
        getattr(api_instance, method_name)(*args, **kwargs)
        
    if not worker_captured:
        raise Exception("Nenhum worker capturado")
        
    mock_context = MagicMock()
    return worker_captured[0](mock_context)

@patch("modules.otimizacao.executar_otimizacao_geral")
def test_initial_state_rejects_mutation(mock_otim, api):
    with pytest.raises(ProtectionError):
        _run_sync(api, "executar_otimizacao_geral")
    mock_otim.assert_not_called()

@patch("modules.otimizacao.criar_ponto_restauracao")
def test_successful_restore_point_marks_created(mock_criar, api):
    mock_criar.return_value = {"ok": True, "codigo": "COMMAND_OK"}
    res = _run_sync(api, "criar_ponto_restauracao")
    assert res["ok"] is True
    assert api._protection_state == "restore_created"
    
    # Agora a mutação deve funcionar
    with patch("modules.otimizacao.executar_otimizacao_geral") as mock_otim:
        mock_otim.return_value = {"ok": True}
        _run_sync(api, "executar_otimizacao_geral")
        mock_otim.assert_called_once()

@patch("modules.otimizacao.criar_ponto_restauracao")
def test_failed_restore_does_not_mark_protected(mock_criar, api):
    mock_criar.return_value = {"ok": False, "codigo": "COMMAND_FAILED"}
    res = _run_sync(api, "criar_ponto_restauracao")
    assert res["ok"] is False
    assert api._protection_state == "not_attempted"
    assert api._restore_attempt_failed is True
    
    # Mutação continua bloqueada
    with pytest.raises(ProtectionError):
        _run_sync(api, "executar_otimizacao_geral")

def test_confirmar_risco_before_failed_attempt_rejected(api):
    res = api.confirmar_risco_protecao()
    assert res["ok"] is False
    assert api._protection_state == "not_attempted"

@patch("modules.otimizacao.criar_ponto_restauracao")
def test_confirmar_risco_after_failed_attempt_sets_accepted(mock_criar, api):
    mock_criar.return_value = {"ok": False}
    _run_sync(api, "criar_ponto_restauracao")
    
    res = api.confirmar_risco_protecao()
    assert res["ok"] is True
    assert api._protection_state == "risk_accepted"
    
    # Mutação deve funcionar agora
    with patch("modules.otimizacao.executar_otimizacao_geral") as mock_otim:
        mock_otim.return_value = {"ok": True}
        _run_sync(api, "executar_otimizacao_geral")
        mock_otim.assert_called_once()

def test_endpoint_coverage(api):
    # Ensure all these endpoints require protection
    protected_endpoints = [
        "executar_otimizacao_geral",
        "executar_otimizacao_gaming",
        "executar_rotina_completa",
    ]
    
    for ep in protected_endpoints:
        with pytest.raises(ProtectionError):
            _run_sync(api, ep)

    with pytest.raises(ProtectionError):
        _run_sync(api, "desativar_servico", "DiagTrack")

    with pytest.raises(ProtectionError):
        _run_sync(api, "ativar_servico", "DiagTrack")
