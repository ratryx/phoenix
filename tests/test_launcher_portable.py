import pytest
import sys
from unittest.mock import patch, MagicMock

import launcher
from modules.shared import IS_PORTABLE

@pytest.fixture
def mock_portable_env(monkeypatch):
    monkeypatch.setattr("modules.shared.IS_PORTABLE", True)
    monkeypatch.setattr("launcher.HAS_CONSOLE", True)
    # Evita sys.exit matar os testes
    monkeypatch.setattr("sys.exit", MagicMock())

    # Mocks das telas do console
    monkeypatch.setattr("launcher.console.print", MagicMock())
    monkeypatch.setattr("launcher.console.clear", MagicMock())

    # Mock do gui_app e cli_app para podermos verificar chamadas
    monkeypatch.setattr("modules.cli_app.iniciar", MagicMock())
    monkeypatch.setattr("modules.gui_app.iniciar", MagicMock())

def test_launcher_existing_client_success(mock_portable_env, monkeypatch):
    # Mock selecao_cliente para retornar algo estruturado
    monkeypatch.setattr(
        "modules.selecao_cliente.exibir_selecao_cli",
        lambda: {"id": "cliente-alvo", "nome": "Cliente Alvo"}
    )

    # Mock do selecionar_cliente_portable
    mock_selecionar = MagicMock(return_value={"ok": True, "cliente": {"id": "cliente-alvo"}})
    monkeypatch.setattr("modules.shared.selecionar_cliente_portable", mock_selecionar)

    res = launcher._iniciar_modo_portable()
    assert res is True
    mock_selecionar.assert_called_once_with("cliente-alvo")

def test_launcher_new_client_success(mock_portable_env, monkeypatch):
    # Idem ao anterior, mas simulando criacao (exibir_selecao_cli cuida de chamar criar_cliente)
    monkeypatch.setattr(
        "modules.selecao_cliente.exibir_selecao_cli",
        lambda: {"id": "cliente-novo", "nome": "Novo"}
    )
    mock_selecionar = MagicMock(return_value={"ok": True, "cliente": {"id": "cliente-novo"}})
    monkeypatch.setattr("modules.shared.selecionar_cliente_portable", mock_selecionar)

    res = launcher._iniciar_modo_portable()
    assert res is True
    mock_selecionar.assert_called_once_with("cliente-novo")

def test_launcher_selection_failure(mock_portable_env, monkeypatch):
    monkeypatch.setattr(
        "modules.selecao_cliente.exibir_selecao_cli",
        lambda: {"id": "invalido", "nome": "Invalido"}
    )
    mock_selecionar = MagicMock(return_value={"ok": False, "erro": "CLIENT_NOT_FOUND"})
    monkeypatch.setattr("modules.shared.selecionar_cliente_portable", mock_selecionar)

    # Aqui o launcher deve chamar sys.exit(1)
    launcher._iniciar_modo_portable()

    import sys
    sys.exit.assert_called_once_with(1)

def test_launcher_cancellation(mock_portable_env, monkeypatch):
    monkeypatch.setattr("modules.selecao_cliente.exibir_selecao_cli", lambda: None)

    res = launcher._iniciar_modo_portable()
    assert res is False
