import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from modules.gui.api import PhoenixAPI
from modules.core.windows_command import CommandResult

@pytest.fixture
def api():
    hw_info_mock = MagicMock()
    return PhoenixAPI(hw_info=hw_info_mock)

@patch("modules.logs.obter_pasta_logs")
@patch("modules.core.windows_command.run_windows_command")
def test_abrir_pasta_relatorio_sucesso(mock_run_command, mock_obter_pasta_logs, api):
    mock_pasta = MagicMock(spec=Path)
    mock_pasta.exists.return_value = True
    mock_obter_pasta_logs.return_value = mock_pasta
    
    mock_run_command.return_value = CommandResult(
        ok=True, code="COMMAND_OK", returncode=0, stdout="", stderr="", timed_out=False, cancelled=False, duration_ms=0, termination_ok=True
    )
    
    res = api.abrir_pasta_relatorio("atendimento_123")
    
    assert res["ok"] is True
    assert res["codigo"] == 0
    mock_run_command.assert_called_once()
    args = mock_run_command.call_args[0][0]
    assert "explorer" in args

@patch("modules.logs.obter_pasta_logs")
def test_abrir_pasta_relatorio_inexistente(mock_obter_pasta_logs, api):
    mock_pasta = MagicMock(spec=Path)
    mock_pasta.exists.return_value = False
    mock_obter_pasta_logs.return_value = mock_pasta
    
    res = api.abrir_pasta_relatorio("atendimento_123")
    assert res["ok"] is False
    assert "Pasta não encontrada" in res["erro"]

@patch("modules.logs.obter_pasta_logs")
@patch("modules.core.windows_command.run_windows_command")
def test_abrir_relatorio_html_sucesso(mock_run_command, mock_obter_pasta_logs, api):
    mock_pasta = MagicMock(spec=Path)
    mock_arquivo = MagicMock(spec=Path)
    mock_arquivo.exists.return_value = True
    mock_pasta.__truediv__.return_value = mock_arquivo
    mock_obter_pasta_logs.return_value = mock_pasta
    
    mock_run_command.return_value = CommandResult(
        ok=True, code="COMMAND_OK", returncode=0, stdout="", stderr="", timed_out=False, cancelled=False, duration_ms=0, termination_ok=True
    )
    
    res = api.abrir_relatorio_html("atendimento_123")
    
    assert res["ok"] is True
    mock_run_command.assert_called_once()
    
@patch("modules.logs.obter_pasta_logs")
def test_abrir_relatorio_html_inexistente(mock_obter_pasta_logs, api):
    mock_pasta = MagicMock(spec=Path)
    mock_arquivo = MagicMock(spec=Path)
    mock_arquivo.exists.return_value = False
    mock_pasta.__truediv__.return_value = mock_arquivo
    mock_obter_pasta_logs.return_value = mock_pasta
    
    res = api.abrir_relatorio_html("atendimento_123")
    assert res["ok"] is False
    assert "Relatório HTML não encontrado" in res["erro"]
