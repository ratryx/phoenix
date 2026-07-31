import pytest
from unittest.mock import patch
from modules.smart import _consultar_confiabilidade_disco

@patch("modules.smart.run_windows_command")
def test_smart_device_id_validation_valid(mock_run):
    _consultar_confiabilidade_disco("0")
    assert mock_run.called
    assert "DeviceId -eq '0'" in mock_run.call_args[0][0][3]
    
    _consultar_confiabilidade_disco("123")
    assert mock_run.called
    assert "DeviceId -eq '123'" in mock_run.call_args[0][0][3]

@patch("modules.smart.run_windows_command")
def test_smart_device_id_validation_malicious(mock_run):
    res = _consultar_confiabilidade_disco("0'; Write-Host 'hacked")
    assert res is None
    assert not mock_run.called

@patch("modules.smart.run_windows_command")
def test_smart_device_id_validation_malformed(mock_run):
    res = _consultar_confiabilidade_disco("C:")
    assert res is None
    assert not mock_run.called
    
    res = _consultar_confiabilidade_disco(None)
    assert res is None
    assert not mock_run.called
