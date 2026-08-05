import pytest
from unittest.mock import patch, MagicMock
from modules.limpeza import executar_limpeza_completa

def test_cli_limpeza_integral(capsys):
    with patch("modules.limpeza.executar_limpeza") as mock_exec:
        mock_exec.return_value = {
            "ok": True,
            "parcial": False,
            "espaco_liberado_bytes": 1024 * 1024 * 5, # 5 MB
            "espaco_liberado_mb": 5.0,
            "categorias": []
        }
        bytes_liberados = executar_limpeza_completa()
        
    assert bytes_liberados == 1024 * 1024 * 5
    captured = capsys.readouterr()
    assert "Limpeza concluída! Total liberado" in captured.out

def test_cli_limpeza_parcial(capsys):
    with patch("modules.limpeza.executar_limpeza") as mock_exec:
        mock_exec.return_value = {
            "ok": True,
            "parcial": True,
            "espaco_liberado_bytes": 1024 * 1024 * 2, # 2 MB
            "espaco_liberado_mb": 2.0,
            "categorias": []
        }
        bytes_liberados = executar_limpeza_completa()
        
    assert bytes_liberados == 1024 * 1024 * 2
    captured = capsys.readouterr()
    assert "Limpeza concluída parcialmente!" in captured.out

def test_cli_limpeza_falha(capsys):
    with patch("modules.limpeza.executar_limpeza") as mock_exec:
        mock_exec.return_value = {
            "ok": False,
            "parcial": False,
            "espaco_liberado_bytes": 0,
            "espaco_liberado_mb": 0.0,
            "categorias": []
        }
        bytes_liberados = executar_limpeza_completa()
        
    assert bytes_liberados == 0
    captured = capsys.readouterr()
    assert "Limpeza falhou ou foi cancelada!" in captured.out
