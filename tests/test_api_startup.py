import pytest
from unittest.mock import patch, MagicMock
from modules.gui.api import PhoenixAPI

@patch("modules.otimizacao.listar_itens_inicializacao")
def test_api_listar_inicializacao_sucesso(mock_listar):
    mock_listar.return_value = {"ok": True, "codigo": "COMMAND_OK", "itens": ["Process1", "Process2"]}
    api = PhoenixAPI({})
    res = api.listar_inicializacao()
    assert res == {"ok": True, "codigo": "COMMAND_OK", "itens": ["Process1", "Process2"]}

@patch("modules.otimizacao.listar_itens_inicializacao")
def test_api_listar_inicializacao_vazio(mock_listar):
    mock_listar.return_value = {"ok": True, "codigo": "COMMAND_OK", "itens": [], "mensagem": "Nenhum item encontrado."}
    api = PhoenixAPI({})
    res = api.listar_inicializacao()
    assert res == {"ok": True, "codigo": "COMMAND_OK", "itens": [], "mensagem": "Nenhum item encontrado."}

@patch("modules.otimizacao.listar_itens_inicializacao")
def test_api_listar_inicializacao_falha(mock_listar):
    mock_listar.return_value = {"ok": False, "codigo": "COMMAND_FAILED", "erro": "Falha"}
    api = PhoenixAPI({})
    res = api.listar_inicializacao()
    assert res == {"ok": False, "codigo": "COMMAND_FAILED", "erro": "Falha"}

@patch("modules.otimizacao.listar_itens_inicializacao")
def test_api_listar_inicializacao_timeout(mock_listar):
    mock_listar.return_value = {"ok": False, "codigo": "COMMAND_TIMEOUT", "erro": "Tempo limite excedido."}
    api = PhoenixAPI({})
    res = api.listar_inicializacao()
    assert res == {"ok": False, "codigo": "COMMAND_TIMEOUT", "erro": "Tempo limite excedido."}

@patch("modules.otimizacao.listar_itens_inicializacao")
def test_api_listar_inicializacao_cancelado(mock_listar):
    mock_listar.return_value = {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "Cancelado"}
    api = PhoenixAPI({})
    res = api.listar_inicializacao()
    assert res == {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "Cancelado"}

