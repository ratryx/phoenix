import pytest
from unittest.mock import patch, mock_open, call, MagicMock
from pathlib import Path
import json
from modules.servicos import _salvar_estado_servico, desativar_servico, ativar_servico
from modules.core.windows_command import CommandResult

@pytest.fixture
def mock_backup_path(tmp_path):
    with patch("modules.servicos._obter_arquivo_backup_servicos") as mock_path:
        mock_path.return_value = tmp_path / "servicos_backup.json"
        yield mock_path.return_value

def fake_res(ok=True, stdout=""):
    return CommandResult(code="COMMAND_OK" if ok else "COMMAND_FAILED", ok=ok, stdout=stdout, stderr="", returncode=0 if ok else 1, timed_out=False, cancelled=False, duration_ms=10, termination_ok=True)

def test_salvar_estado_manual_stopped(mock_backup_path):
    with patch("modules.servicos.run_windows_command") as mock_run:
        def side_effect(cmd, **kwargs):
            if cmd[1] == "qc":
                return fake_res(stdout="TIPO_DE_INICIO : 3 DEMAND_START")
            elif cmd[1] == "query":
                return fake_res(stdout="STATE : 1 STOPPED")
            return fake_res()
        mock_run.side_effect = side_effect
        
        res = _salvar_estado_servico("DiagTrack")
        assert res["ok"] is True
        
        saved = json.loads(mock_backup_path.read_text(encoding="utf-8"))
        assert saved["DiagTrack"] == {"start_type": "demand", "status": "parado"}

def test_salvar_estado_auto_running(mock_backup_path):
    with patch("modules.servicos.run_windows_command") as mock_run:
        def side_effect(cmd, **kwargs):
            if cmd[1] == "qc":
                return fake_res(stdout="TIPO_DE_INICIO : 2 AUTO_START")
            elif cmd[1] == "query":
                return fake_res(stdout="STATE : 4 RUNNING")
            return fake_res()
        mock_run.side_effect = side_effect
        
        res = _salvar_estado_servico("DiagTrack")
        assert res["ok"] is True
        
        saved = json.loads(mock_backup_path.read_text(encoding="utf-8"))
        assert saved["DiagTrack"] == {"start_type": "auto", "status": "rodando"}

def test_salvar_estado_delayed_auto(mock_backup_path):
    with patch("modules.servicos.run_windows_command") as mock_run:
        def side_effect(cmd, **kwargs):
            if cmd[1] == "qc":
                return fake_res(stdout="TIPO_DE_INICIO : 2 AUTO_START (DELAYED)")
            elif cmd[1] == "query":
                return fake_res(stdout="STATE : 4 RUNNING")
            return fake_res()
        mock_run.side_effect = side_effect
        
        res = _salvar_estado_servico("DiagTrack")
        assert res["ok"] is True
        
        saved = json.loads(mock_backup_path.read_text(encoding="utf-8"))
        assert saved["DiagTrack"] == {"start_type": "delayed-auto", "status": "rodando"}

def test_salvar_estado_query_failure(mock_backup_path):
    with patch("modules.servicos.run_windows_command") as mock_run:
        def side_effect(cmd, **kwargs):
            if cmd[1] == "qc":
                return fake_res(ok=False)
            return fake_res()
        mock_run.side_effect = side_effect
        
        res = _salvar_estado_servico("DiagTrack")
        assert res["ok"] is False
        assert not mock_backup_path.exists()
        
def test_salvar_estado_write_failure(mock_backup_path):
    with patch("modules.servicos.run_windows_command") as mock_run, \
         patch("builtins.open", side_effect=PermissionError("Acesso negado")):
        def side_effect(cmd, **kwargs):
            if cmd[1] == "qc":
                return fake_res(stdout="TIPO_DE_INICIO : 2 AUTO_START")
            elif cmd[1] == "query":
                return fake_res(stdout="STATE : 4 RUNNING")
            return fake_res()
        mock_run.side_effect = side_effect
        
        res = _salvar_estado_servico("DiagTrack")
        assert res["ok"] is False

@patch("modules.servicos._salvar_estado_servico")
@patch("modules.servicos.run_windows_command")
def test_desativar_zero_mutation_on_state_failure(mock_run, mock_salvar, mock_backup_path):
    mock_salvar.return_value = {"ok": False, "erro": "Simulated fail"}
    
    res = desativar_servico("DiagTrack")
    assert res["ok"] is False
    assert res["codigo"] == "BACKUP_FAILED"
    mock_run.assert_not_called()

@patch("modules.servicos.run_windows_command")
def test_ativar_no_backup_fails_closed(mock_run, mock_backup_path):
    res = ativar_servico("DiagTrack")
    assert res["ok"] is False
    assert res["codigo"] == "NO_BACKUP"
    mock_run.assert_not_called()

@patch("modules.servicos.run_windows_command")
def test_ativar_restores_and_consumes_backup(mock_run, mock_backup_path):
    # Setup backup
    mock_backup_path.write_text(json.dumps({"DiagTrack": {"start_type": "demand", "status": "parado"}}), encoding="utf-8")
    
    mock_run.return_value = fake_res()
    
    res = ativar_servico("DiagTrack")
    assert res["ok"] is True
    
    # Must have called config with start= demand (note the space is not explicitly required in the array, wait...)
    # The command array is ["sc", "config", "DiagTrack", "start=", "demand"]
    mock_run.assert_any_call(["sc", "config", "DiagTrack", "start=", "demand"], operation_name="Restaurar config DiagTrack", timeout_seconds=15.0, cancel_event=None)
    
    # Assert not started
    assert mock_run.call_count == 1
    
    # Assert backup consumed
    saved = json.loads(mock_backup_path.read_text(encoding="utf-8"))
    assert "DiagTrack" not in saved

@patch("modules.servicos.run_windows_command")
def test_ativar_corrupted_backup_fails_closed(mock_run, mock_backup_path):
    mock_backup_path.write_text("{ corrupt json", encoding="utf-8")
    
    res = ativar_servico("DiagTrack")
    assert res["ok"] is False
    assert res["codigo"] == "NO_BACKUP"
    mock_run.assert_not_called()
