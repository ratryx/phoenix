import pytest
from unittest.mock import patch
from modules.otimizacao import _executar_comando, executar_verificacao_integridade_sistema
from modules.core.windows_command import CommandResult

@patch("modules.otimizacao.run_windows_command")
def test_executar_comando_default_timeout(mock_run):
    mock_run.return_value = CommandResult(code="COMMAND_OK", ok=True, stdout="", stderr="", returncode=0, timed_out=False, cancelled=False, duration_ms=10, termination_ok=True)
    _executar_comando(["echo", "oi"], "Teste")
    
    # Defaults to 30s
    mock_run.assert_called_once()
    assert mock_run.call_args[1].get("timeout_seconds") == 30.0

@patch("modules.otimizacao._executar_comando")
def test_integridade_timeouts(mock_exec):
    mock_exec.return_value = {"ok": True, "codigo": "COMMAND_OK"}
    
    executar_verificacao_integridade_sistema()
    
    # Should be called twice (DISM, SFC) with 900s timeout
    assert mock_exec.call_count == 2
    for call in mock_exec.call_args_list:
        kwargs = call[1]
        assert kwargs.get("timeout_seconds") == 900.0
