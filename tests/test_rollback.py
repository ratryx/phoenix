import pytest
from unittest.mock import patch, MagicMock
from modules.rollback import _restaurar_valor_registro, _restaurar_plano_energia

def test_rollback_invalid_path_or_value():
    # Caminho não está em CHAVES_RASTREADAS
    res = _restaurar_valor_registro("HKCU:\\Caminho\\Invalido", "Valor1", "1", "registro_dword")
    assert res is False

    # Valor não está em CHAVES_RASTREADAS
    res = _restaurar_valor_registro("HKCU:\\Software\\Microsoft\\GameBar", "ValorInvalido", "1", "registro_dword")
    assert res is False

@patch("modules.rollback.winreg.OpenKey")
def test_rollback_malformed_dword(mock_open):
    # Oversized DWORD
    res = _restaurar_valor_registro("HKCU:\\Software\\Microsoft\\GameBar", "AllowAutoGameMode", "4294967296", "registro_dword")
    assert res is False

    # Negative DWORD
    res = _restaurar_valor_registro("HKCU:\\Software\\Microsoft\\GameBar", "AllowAutoGameMode", "-1", "registro_dword")
    assert res is False

    # Not an integer
    res = _restaurar_valor_registro("HKCU:\\Software\\Microsoft\\GameBar", "AllowAutoGameMode", "abc", "registro_dword")
    assert res is False

@patch("modules.rollback.winreg.OpenKey")
def test_rollback_malformed_binary(mock_open):
    # Empty
    res = _restaurar_valor_registro("HKCU:\\Control Panel\\Desktop", "UserPreferencesMask", "", "registro_binario")
    assert res is False

    # Empty token
    res = _restaurar_valor_registro("HKCU:\\Control Panel\\Desktop", "UserPreferencesMask", "144,,3", "registro_binario")
    assert res is False

    # Outside byte range
    res = _restaurar_valor_registro("HKCU:\\Control Panel\\Desktop", "UserPreferencesMask", "256", "registro_binario")
    assert res is False

    # Outside byte range negative
    res = _restaurar_valor_registro("HKCU:\\Control Panel\\Desktop", "UserPreferencesMask", "-1", "registro_binario")
    assert res is False

@patch("modules.rollback.run_windows_command")
def test_rollback_malformed_guid(mock_run):
    res = _restaurar_plano_energia("invalido")
    assert res is False
    assert not mock_run.called
