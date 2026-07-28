import pytest
from pathlib import Path
import uuid
import os
from unittest.mock import patch

from modules.shared import (
    criar_cliente_portable,
    selecionar_cliente_portable,
    listar_clientes_portable,
    _resolver_pasta_cliente,
    obter_pasta_base,
    obter_pasta_clientes
)

from modules.selecao_cliente import exibir_selecao_cli

@pytest.fixture
def mock_portable(monkeypatch, tmp_path):
    monkeypatch.setattr("modules.shared.IS_PORTABLE", True)

    fake_exe_dir = tmp_path / "fake_exe"
    fake_exe_dir.mkdir()

    def mock_obter_pasta_exe():
        return fake_exe_dir

    monkeypatch.setattr("modules.shared.obter_pasta_exe", mock_obter_pasta_exe)
    return fake_exe_dir

def test_criar_cliente_portable_invalid_names(mock_portable):
    assert criar_cliente_portable("")["ok"] is False
    assert criar_cliente_portable("   ")["ok"] is False
    assert criar_cliente_portable("\x00")["ok"] is False
    assert criar_cliente_portable("a" * 101)["ok"] is False

    # Valida acentos e emojis
    res = criar_cliente_portable("José 🚀")
    assert res["ok"] is True
    assert res["cliente"]["nome_display"] == "José 🚀"
    assert "jose" in res["cliente"]["id"]

def test_id_collision_retry(mock_portable, monkeypatch):
    import uuid
    # Create the colliding directory first
    colliding_id = "teste-aaaabbbb"
    colliding_dir = obter_pasta_clientes() / colliding_id
    colliding_dir.mkdir(parents=True)

    class MockUUID:
        def __init__(self):
            self.calls = 0
            self.uuids = ["aaaabbbb", "ccccdddd"]
        def __call__(self):
            class Fake:
                hex = self.uuids[self.calls]
            self.calls += 1
            return Fake()

    mock_uuid = MockUUID()
    monkeypatch.setattr("uuid.uuid4", mock_uuid)

    res = criar_cliente_portable("Teste")
    assert res["ok"] is True

    assert mock_uuid.calls == 2
    assert "ccccdddd" in res["cliente"]["id"]

    # The existing metadata should be untouched (it didn't exist, but the folder is independent)
    assert (obter_pasta_clientes() / res["cliente"]["id"]).exists()
    assert res["cliente"]["id"] != colliding_id

def test_id_collision_exhaustion(mock_portable, monkeypatch):
    import uuid
    colliding_id = "teste-aaaabbbb"
    colliding_dir = obter_pasta_clientes() / colliding_id
    colliding_dir.mkdir(parents=True)

    # Pre-create a meta.json to prove it's untouched
    meta_path = colliding_dir / "meta.json"
    with open(meta_path, "w") as f:
        f.write('{"id": "original"}')

    class MockUUID:
        def __call__(self):
            class Fake:
                hex = "aaaabbbb"
            return Fake()

    monkeypatch.setattr("uuid.uuid4", MockUUID())

    res = criar_cliente_portable("Teste")
    assert res["ok"] is False
    assert res["erro"] == "CLIENT_CREATE_FAILED"

    # Verify meta.json is unmodified
    with open(meta_path, "r") as f:
        assert f.read() == '{"id": "original"}'

def test_path_resolver_containment(mock_portable):
    # Cria um id normal
    res = criar_cliente_portable("Normal")
    id_cliente = res["cliente"]["id"]

    # O diretório do cliente existe
    pasta = _resolver_pasta_cliente(id_cliente, must_exist=True)
    assert pasta is not None
    assert pasta.name == id_cliente

    # Tenta usar um ID com directory traversal
    assert _resolver_pasta_cliente("../fake_exe") is None

    # Tenta usar um sibling com mesmo prefixo usando monkeypatch direto no path
    raiz = obter_pasta_clientes()
    malicioso = raiz.parent / (raiz.name + "-malicioso")
    malicioso.mkdir()

    # Mock _validar_id_cliente to allow our attack
    import modules.shared
    original_val = modules.shared._validar_id_cliente
    modules.shared._validar_id_cliente = lambda x: True

    # Send a payload that tries to reach the sibling
    payload = f"../{malicioso.name}"
    assert _resolver_pasta_cliente(payload) is None

    modules.shared._validar_id_cliente = original_val

def test_cli_existing_client(mock_portable, monkeypatch):
    res1 = criar_cliente_portable("Cliente Alpha")
    res2 = criar_cliente_portable("Cliente Alpha") # Mesmo nome, IDs diferentes

    # Mock do input para selecionar o cliente 2
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: "2")

    escolha = exibir_selecao_cli()
    assert escolha["id"] in [res1["cliente"]["id"], res2["cliente"]["id"]]
    assert escolha["nome"] == "Cliente Alpha"

    res_sel = selecionar_cliente_portable(escolha["id"])
    assert res_sel["ok"] is True
    from modules.shared import CLIENTE_ATIVO_ID
    assert CLIENTE_ATIVO_ID in [res1["cliente"]["id"], res2["cliente"]["id"]]

def test_cli_new_client(mock_portable, monkeypatch):
    # Lista começa vazia, tenta escolher 0 (novo) depois dá o nome

    inputs = ["Novo Cliente CLI"]
    def mock_ask(*args, **kwargs):
        if inputs:
            return inputs.pop(0)
        return ""

    monkeypatch.setattr("rich.prompt.Prompt.ask", mock_ask)

    escolha = exibir_selecao_cli()
    assert escolha is not None
    assert escolha["nome"] == "Novo Cliente CLI"
    assert "novo-cliente" in escolha["id"]

    # Verifica que salvou no shared
    clientes = listar_clientes_portable()
    assert len(clientes) == 1
    assert clientes[0]["id"] == escolha["id"]

def test_listar_clientes_out_of_portable(monkeypatch):
    monkeypatch.setattr("modules.shared.IS_PORTABLE", False)
    res = listar_clientes_portable()
    assert isinstance(res, dict)
    assert res["ok"] is False
    assert res["codigo"] == "PORTABLE_MODE_REQUIRED"
