import pytest
from unittest.mock import patch, mock_open, call, MagicMock
from pathlib import Path
import json
from modules.servicos import _salvar_estado_servico, desativar_servico, restaurar_servico, iniciar_servico, _atomic_write_json
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
         patch("modules.servicos._atomic_write_json", return_value=False):
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
def test_restaurar_no_backup_fails_closed(mock_run, mock_backup_path):
    res = restaurar_servico("DiagTrack")
    assert res["ok"] is False
    assert res["codigo"] == "NO_BACKUP"
    mock_run.assert_not_called()

@patch("modules.servicos.run_windows_command")
def test_restaurar_restores_and_consumes_backup(mock_run, mock_backup_path):
    # Setup backup
    mock_backup_path.write_text(json.dumps({"DiagTrack": {"start_type": "demand", "status": "parado"}}), encoding="utf-8")

    mock_run.return_value = fake_res()

    res = restaurar_servico("DiagTrack")
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
def test_restaurar_corrupted_backup_fails_closed(mock_run, mock_backup_path):
    mock_backup_path.write_text("{ corrupt json", encoding="utf-8")

    res = restaurar_servico("DiagTrack")
    assert res["ok"] is False
    assert res["codigo"] == "NO_BACKUP"
    mock_run.assert_not_called()

@patch("modules.servicos.run_windows_command")
def test_iniciar_servico_success(mock_run):
    mock_run.return_value = fake_res()
    res = iniciar_servico("DiagTrack")
    assert res["ok"] is True
    # Should only run 'start', no 'config'
    mock_run.assert_called_once_with(["sc", "start", "DiagTrack"], operation_name="Iniciar manual DiagTrack", timeout_seconds=15.0, acceptable_returncodes=(0, 1056), cancel_event=None)

def test_atomic_write_json(tmp_path):
    arquivo = tmp_path / "teste_atomic.json"
    dados = {"a": 1}
    assert _atomic_write_json(arquivo, dados) is True
    assert json.loads(arquivo.read_text(encoding="utf-8")) == dados

    # Must use temporary file, ensure it's deleted
    assert not (tmp_path / "teste_atomic.tmp").exists()

@patch("os.replace", side_effect=PermissionError("Mocked replace failure"))
def test_atomic_write_json_failure(mock_replace, tmp_path):
    arquivo = tmp_path / "teste_atomic2.json"
    arquivo.write_text('{"velho": 2}')
    dados = {"a": 1}
    assert _atomic_write_json(arquivo, dados) is False
    # Original should be intact
    assert json.loads(arquivo.read_text(encoding="utf-8")) == {"velho": 2}
    # Tmp file should be deleted
    assert not (tmp_path / "teste_atomic2.tmp").exists()
