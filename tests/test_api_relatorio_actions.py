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
@patch("modules.core.windows_command.run_windows_command", autospec=True)
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
    kwargs = mock_run_command.call_args[1]
    assert kwargs.get("operation_name") == "abrir_pasta_relatorio"
    assert kwargs.get("timeout_seconds") == 5.0
    args = kwargs.get("args") or mock_run_command.call_args[0][0]
    assert args == ["explorer.exe", str(mock_pasta)]

@patch("modules.logs.obter_pasta_logs")
def test_abrir_pasta_relatorio_inexistente(mock_obter_pasta_logs, api):
    mock_pasta = MagicMock(spec=Path)
    mock_pasta.exists.return_value = False
    mock_obter_pasta_logs.return_value = mock_pasta
    
    res = api.abrir_pasta_relatorio("atendimento_123")
    assert res["ok"] is False
    assert "A pasta de relatórios não foi encontrada" in res["erro"]

@patch("modules.logs.obter_pasta_logs")
@patch("modules.core.windows_command.run_windows_command", autospec=True)
def test_abrir_relatorio_html_sucesso(mock_run_command, mock_obter_pasta_logs, api):
    mock_pasta = MagicMock(spec=Path)
    mock_arquivo = MagicMock(spec=Path)
    mock_arquivo.exists.return_value = True
    mock_arquivo.parent = mock_pasta
    mock_pasta.__truediv__.return_value = mock_arquivo
    mock_obter_pasta_logs.return_value = mock_pasta
    
    mock_run_command.return_value = CommandResult(
        ok=True, code="COMMAND_OK", returncode=0, stdout="", stderr="", timed_out=False, cancelled=False, duration_ms=0, termination_ok=True
    )
    
    res = api.abrir_relatorio_html("atendimento_123")
    
    assert res["ok"] is True
    mock_run_command.assert_called_once()
    kwargs = mock_run_command.call_args[1]
    assert kwargs.get("operation_name") == "abrir_relatorio_html"
    assert kwargs.get("timeout_seconds") == 5.0
    args = kwargs.get("args") or mock_run_command.call_args[0][0]
    assert args == ["explorer.exe", str(mock_arquivo)]
    
@patch("modules.logs.obter_pasta_logs")
def test_abrir_relatorio_html_inexistente(mock_obter_pasta_logs, api):
    mock_pasta = MagicMock(spec=Path)
    mock_arquivo = MagicMock(spec=Path)
    mock_arquivo.exists.return_value = False
    mock_arquivo.parent = mock_pasta
    mock_pasta.__truediv__.return_value = mock_arquivo
    mock_obter_pasta_logs.return_value = mock_pasta
    
    res = api.abrir_relatorio_html("atendimento_123")
    assert res["ok"] is False
    assert "O relatório HTML não foi encontrado" in res["erro"]

def test_abrir_relatorio_html_traversal_blocks(api):
    res = api.abrir_relatorio_html("../../../windows/system32")
    assert res["ok"] is False
    assert "Identificador de atendimento inválido" in res["erro"]
    
def test_abrir_relatorio_html_slashes_blocks(api):
    res = api.abrir_relatorio_html("atendimento/123")
    assert res["ok"] is False
    assert "Identificador de atendimento inválido" in res["erro"]

@patch("modules.logs.obter_pasta_logs")
@patch("modules.core.windows_command.run_windows_command")
def test_abrir_relatorio_html_exception_masking(mock_run_command, mock_obter_pasta_logs, api):
    mock_pasta = MagicMock(spec=Path)
    mock_arquivo = MagicMock(spec=Path)
    mock_arquivo.exists.return_value = True
    mock_arquivo.parent = mock_pasta
    mock_pasta.__truediv__.return_value = mock_arquivo
    mock_obter_pasta_logs.return_value = mock_pasta
    
    mock_run_command.side_effect = Exception("SenhaSecreta123")
    
    res = api.abrir_relatorio_html("atendimento_123")
    assert res["ok"] is False
    assert "Erro interno" in res["erro"]
    assert "SenhaSecreta123" not in res["erro"]
