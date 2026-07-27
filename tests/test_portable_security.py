import os
import shutil
from pathlib import Path
import pytest
import uuid

from modules.shared import (
    _validar_id_cliente,
    criar_cliente_portable,
    obter_pasta_base,
    listar_clientes_portable,
    remover_cliente_portable,
    definir_cliente_ativo,
    IS_PORTABLE
)
from modules.gui.api import PhoenixAPI

# Mock para testes portables
@pytest.fixture
def mock_portable(monkeypatch, tmp_path):
    monkeypatch.setattr("modules.shared.IS_PORTABLE", True)

    # Redireciona o root
    fake_exe_dir = tmp_path / "fake_exe"
    fake_exe_dir.mkdir()

    def mock_obter_pasta_exe():
        return fake_exe_dir

    monkeypatch.setattr("modules.shared.obter_pasta_exe", mock_obter_pasta_exe)

    yield fake_exe_dir

def test_id_validation():
    assert _validar_id_cliente("joao-123") is True
    assert _validar_id_cliente("cliente") is True
    assert _validar_id_cliente("") is False
    assert _validar_id_cliente(None) is False
    assert _validar_id_cliente("..") is False
    assert _validar_id_cliente("../cliente") is False
    assert _validar_id_cliente("C:\\windows") is False
    assert _validar_id_cliente("CON") is False
    assert _validar_id_cliente("prn") is False
    assert _validar_id_cliente("a" * 101) is False

def test_criar_cliente_portable_valido(mock_portable):
    meta = criar_cliente_portable("João Silva")
    assert "joao-silva" in meta["id"]
    assert meta["nome_display"] == "João Silva"

    pasta = obter_pasta_base(meta["id"])
    assert pasta.exists()
    assert (pasta / "meta.json").exists()

def test_criar_cliente_portable_nome_invalido(mock_portable):
    meta = criar_cliente_portable("<script>alert(1)</script>")
    assert "scriptalert1script" in meta["id"]

    meta2 = criar_cliente_portable("")
    assert "cliente-" in meta2["id"]

    meta3 = criar_cliente_portable("..//--  ")
    assert "cliente-" in meta3["id"]

def test_path_traversal_obter_pasta_base(mock_portable):
    with pytest.raises(ValueError, match="ID de cliente inválido"):
        obter_pasta_base("..")

    with pytest.raises(ValueError, match="ID de cliente inválido"):
        obter_pasta_base("C:\\")

def test_legacy_client_compatibility(mock_portable):
    # Criar um cliente legado sem meta.json
    pasta_clientes = mock_portable / "dados" / "clientes"
    pasta_clientes.mkdir(parents=True)
    pasta_legada = pasta_clientes / "joao-silva-antigo"
    pasta_legada.mkdir()

    clientes = listar_clientes_portable()
    assert len(clientes) == 1
    assert clientes[0]["id"] == "joao-silva-antigo"
    assert clientes[0]["nome"] == "Joao Silva Antigo"

    # Criar um que é só pasta, tentar definir ativo
    definir_cliente_ativo("joao-silva-antigo", "João")
    from modules.shared import CLIENTE_ATIVO_ID
    assert CLIENTE_ATIVO_ID == "joao-silva-antigo"

def test_remover_cliente_portable(mock_portable):
    meta = criar_cliente_portable("Para Remover")
    id_cliente = meta["id"]

    res = remover_cliente_portable(id_cliente)
    assert res["ok"] is True

    res_not_found = remover_cliente_portable(id_cliente)
    assert res_not_found["ok"] is False
    assert res_not_found["erro"] == "CLIENT_NOT_FOUND"

def test_remover_cliente_portable_traversal(mock_portable):
    res = remover_cliente_portable("..")
    assert res["ok"] is False
    assert res["erro"] == "INVALID_CLIENT_ID"

    # Mesmo se bypassar validação de string (usando hack), deve ser pego
    import modules.shared as ms
    original_val = ms._validar_id_cliente
    ms._validar_id_cliente = lambda x: True # forçar bypass string

    res2 = remover_cliente_portable("..")
    assert res2["ok"] is False
    assert res2["erro"] == "CLIENT_DELETE_FAILED"

    ms._validar_id_cliente = original_val

def test_api_integration(mock_portable):
    api = PhoenixAPI(hw_info={})

    res_criar = api.criar_cliente_portable("Novo Cliente API")
    assert res_criar["ok"] is True
    id_cliente = res_criar["cliente"]["id"]

    res_selecionar = api.selecionar_cliente(id_cliente)
    assert res_selecionar["ok"] is True
    assert res_selecionar["cliente"]["nome"] == "Novo Cliente API"

    res_remover = api.remover_cliente_portable(id_cliente)
    assert res_remover["ok"] is True

def test_atomic_write_failure(mock_portable, monkeypatch):
    import os
    original_replace = os.replace
    def fake_replace(src, dst):
        raise OSError("Mock error replacing file")
    monkeypatch.setattr(os, "replace", fake_replace)

    meta = criar_cliente_portable("Atomic Fail")
    assert meta.get("ok") is False
    assert meta.get("erro") == "PERSISTENCE_WRITE_FAILED"

def test_junction_rejection(mock_portable, monkeypatch):
    import os
    import modules.shared as ms
    original_isjunction = getattr(os.path, 'isjunction', lambda p: False)

    def fake_isjunction(p):
        if "junction-fake" in str(p):
            return True
        return original_isjunction(p)
    monkeypatch.setattr(os.path, "isjunction", fake_isjunction, raising=False)

    # Bypass creating folder if it fails
    # Let's just create a folder directly
    pasta = ms.obter_pasta_clientes() / "junction-fake"
    pasta.mkdir(parents=True, exist_ok=True)

    res = ms.remover_cliente_portable("junction-fake")
    assert res["ok"] is False
    assert res["erro"] == "CLIENT_NOT_FOUND"

def test_api_portable_mode_required(mock_portable, monkeypatch):
    # Simulate not portable mode
    monkeypatch.setattr("modules.shared.IS_PORTABLE", False)
    api = PhoenixAPI(hw_info={})

    res = api.selecionar_cliente("algum-id")
    assert res["ok"] is False
    assert res["codigo"] == "PORTABLE_MODE_REQUIRED"

    res2 = api.remover_cliente_portable("algum-id")
    assert res2["ok"] is False
    assert res2["codigo"] == "PORTABLE_MODE_REQUIRED"

def test_active_client_state(mock_portable):
    api = PhoenixAPI(hw_info={})
    res_criar = api.criar_cliente_portable("Estado Ativo")
    id_cliente = res_criar["cliente"]["id"]

    api.selecionar_cliente(id_cliente)

    from modules.shared import CLIENTE_ATIVO_ID, CLIENTE_ATIVO_NOME
    assert CLIENTE_ATIVO_ID == id_cliente
    assert CLIENTE_ATIVO_NOME == "Estado Ativo"

def test_metadata_id_mismatch(mock_portable):
    import modules.shared as ms
    meta = ms.criar_cliente_portable('Cliente A')
    id_a = meta['id']

    # Simulate malicious meta.json
    meta_file = mock_portable / 'dados' / 'clientes' / id_a / 'meta.json'
    import json
    with open(meta_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['id'] = 'cliente-b-12345678'
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    clientes = ms.listar_clientes_portable()
    assert len(clientes) == 1
    assert clientes[0]['id'] == id_a  # Must ignore the malicious ID

def test_malicious_metadata_id(mock_portable):
    import modules.shared as ms
    meta = ms.criar_cliente_portable('Cliente Traversal')
    id_c = meta['id']

    meta_file = mock_portable / 'dados' / 'clientes' / id_c / 'meta.json'
    import json
    with open(meta_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['id'] = '../windows'
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    clientes = ms.listar_clientes_portable()
    assert clientes[0]['id'] == id_c

def test_selection_persistence_failure_rollback(mock_portable, monkeypatch):
    import modules.shared as ms
    from modules.gui.api import PhoenixAPI
    import os

    ms.criar_cliente_portable('Normal Client')
    clientes = ms.listar_clientes_portable()
    id_normal = clientes[0]['id']

    ms.CLIENTE_ATIVO_ID = 'old-id'
    ms.CLIENTE_ATIVO_NOME = 'Old Name'
    ms.CACHE_DIR = mock_portable / 'old-cache'

    # Mock write failure
    original_replace = getattr(os, 'replace', None)
    def fake_replace(src, dst):
        raise OSError('Disk full')
    monkeypatch.setattr(os, 'replace', fake_replace, raising=False)

    api = PhoenixAPI(hw_info={})
    res = api.selecionar_cliente(id_normal)

    assert res['ok'] is False
    assert res['codigo'] == 'PERSISTENCE_WRITE_FAILED'

    # Assert rollback/unchanged
    assert ms.CLIENTE_ATIVO_ID == 'old-id'
    assert ms.CLIENTE_ATIVO_NOME == 'Old Name'
    assert ms.CACHE_DIR == mock_portable / 'old-cache'

def test_creation_persistence_failure_cleanup(mock_portable, monkeypatch):
    import modules.shared as ms
    import os
    original_replace = getattr(os, 'replace', None)
    def fake_replace(src, dst):
        raise OSError('Disk full')
    monkeypatch.setattr(os, 'replace', fake_replace, raising=False)

    meta = ms.criar_cliente_portable('Falha Criacao')
    assert meta.get('ok') is False
    assert meta.get('erro') == 'PERSISTENCE_WRITE_FAILED'

    clientes = ms.listar_clientes_portable()
    assert len(clientes) == 0

def test_unknown_backend_error_code_normalization(mock_portable):
    from modules.gui.api import PhoenixAPI
    api = PhoenixAPI(hw_info={})
    res = api._make_error('UNKNOWN_WEIRD_ERROR')
    assert res['ok'] is False
    assert res['codigo'] == 'UNKNOWN_ERROR'
    assert res['erro'] == 'Ocorreu um erro interno desconhecido na operação do cliente portátil.'
