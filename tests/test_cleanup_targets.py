import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from modules.core.cleanup_service import (
    _obter_alvos_limpeza,
    _enumerar_seguro,
    executar_limpeza
)
from modules.core.exceptions import JobCancelledError

def test_allowlist_conservative():
    os.environ['LOCALAPPDATA'] = 'C:\\Users\\Test\\AppData\\Local'
    alvos = _obter_alvos_limpeza(incluir_lixeira=False)

    # Must not contain
    proibidos = ['LiveKernelReports', 'Minidump', 'MEMORY.DMP', 'Prefetch', 'lixeira', 'Fontes']
    for p in proibidos:
        for k, v in alvos.items():
            assert p.lower() not in v.get('caminho', '').lower(), f"{p} is present in {k}"
            assert p.lower() not in v.get('padrao', '').lower(), f"{p} is present in {k}"
            assert p.lower() not in k.lower(), f"{p} is present in key {k}"

    # Must contain exact targets
    chaves = set(alvos.keys())
    esperados = {
        'temp_usuario', 'temp_windows', 'wer_archive', 'wer_queue',
        'crash_dumps', 'd3ds_cache', 'thumbcache',
        'cache_chrome', 'cache_edge', 'cache_brave', 'cache_firefox'
    }
    # Note: cache_chrome, etc. only exist if the directory exists. We'll mock os.path.isdir to return True

def test_allowlist_exact_match(monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA', 'C:\\Users\\Test\\AppData\\Local')
    monkeypatch.setattr('os.path.isdir', lambda x: True)

    alvos = _obter_alvos_limpeza(incluir_lixeira=False)
    esperados = {
        'temp_usuario', 'temp_windows', 'wer_archive', 'wer_queue',
        'crash_dumps', 'd3ds_cache', 'thumbcache',
        'cache_chrome', 'cache_edge', 'cache_brave', 'cache_firefox'
    }
    assert set(alvos.keys()) == esperados

def test_temp_manipulated_does_not_alter_target(monkeypatch):
    monkeypatch.setenv('TEMP', 'C:\\Hacked\\Temp')
    with patch('modules.core.cleanup_service.obter_local_appdata', return_value='C:\\Users\\Mocked\\AppData\\Local'):
        alvos = _obter_alvos_limpeza()
        assert 'Hacked' not in alvos['temp_usuario']['caminho']
        assert alvos['temp_usuario']['caminho'] == 'C:\\Users\\Mocked\\AppData\\Local\\Temp'

def test_no_iterdir_or_os_walk():
    with open('modules/core/cleanup_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'Path.iterdir' not in content, "Path.iterdir should not be used"
    assert 'iterdir(' not in content, "iterdir() should not be used"
    assert 'os.walk' not in content, "os.walk should not be used"
    assert 'except Exception: pass' not in content, "except Exception: pass should not be used"

def test_oserror_contabilizado_como_parcial(tmp_path):
    alvos = {
        "teste": {
            "nome": "Teste",
            "caminho": str(tmp_path),
            "raiz_autorizada": str(tmp_path),
            "tipo": "diretorio"
        }
    }

    def mock_scandir(path):
        raise OSError("Access Denied")

    with patch('os.scandir', new=mock_scandir):
        resultado = executar_limpeza(injetar_alvos=alvos)

    assert resultado['parcial'] == True
    assert resultado['arquivos_ignorados'] == 1
    assert 'Raiz do alvo inacessível' in resultado['avisos'][0]

def test_enumerator_not_materializing_tree(tmp_path):
    # Streaming test
    import inspect
    gen = _enumerar_seguro(str(tmp_path), str(tmp_path), None, None)
    assert inspect.isgenerator(gen), "Enumerator must be a generator (streaming)"

import threading
def test_cancelamento_durante_glob(tmp_path):
    (tmp_path / "test.db").write_text("123")
    alvos = {
        "glob_test": {
            "nome": "Glob Test",
            "caminho": str(tmp_path),
            "raiz_autorizada": str(tmp_path),
            "tipo": "glob",
            "padrao": "*.db"
        }
    }
    cancel_event = threading.Event()
    cancel_event.set()
    with pytest.raises(JobCancelledError):
        executar_limpeza(injetar_alvos=alvos, cancel_event=cancel_event)

def test_lixeira_desativada():
    alvos = _obter_alvos_limpeza(incluir_lixeira=False)
    assert 'lixeira' not in alvos

def test_lixeira_ativada():
    alvos = _obter_alvos_limpeza(incluir_lixeira=True)
    assert 'lixeira' in alvos
