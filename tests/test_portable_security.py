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
