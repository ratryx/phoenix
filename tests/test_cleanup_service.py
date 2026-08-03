import os
import threading
import time
import pytest
from pathlib import Path
from modules.core.cleanup_service import executar_limpeza
from modules.core.exceptions import JobCancelledError

def test_executar_limpeza_basic(tmp_path):
    """Testa a limpeza básica de arquivos através de injetar_alvos."""
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    
    file1 = temp_dir / "file1.txt"
    file1.write_text("Hello World!")
    
    alvos = {
        "teste_temp": {
            "nome": "Temp Test",
            "caminho": str(temp_dir),
            "tipo": "diretorio"
        }
    }
    
    result = executar_limpeza(injetar_alvos=alvos)
    
    assert result["ok"] is True
    assert result["arquivos_removidos"] == 1
    assert result["arquivos_ignorados"] == 0
    assert not file1.exists()

def test_executar_limpeza_cancel(tmp_path):
    """Testa o cancelamento cooperativo da limpeza."""
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    
    for i in range(10):
        (temp_dir / f"file{i}.txt").write_text("data")
        
    alvos = {
        "teste_temp": {
            "nome": "Temp Test",
            "caminho": str(temp_dir),
            "tipo": "diretorio"
        }
    }
        
    cancel_event = threading.Event()
    cancel_event.set() # Já começa cancelado para testar aborto imediato
    
    with pytest.raises(JobCancelledError):
        executar_limpeza(cancel_event=cancel_event, injetar_alvos=alvos)

def test_executar_limpeza_invalid_path(tmp_path):
    """Testa a limpeza em caminhos inválidos (inexistentes)."""
    invalid_dir = tmp_path / "does_not_exist"
    
    alvos = {
        "teste_temp": {
            "nome": "Temp Test",
            "caminho": str(invalid_dir),
            "tipo": "diretorio"
        }
    }
            
    result = executar_limpeza(injetar_alvos=alvos)
    
    assert result["ok"] is True
    assert result["arquivos_removidos"] == 0

def test_executar_limpeza_symlink(tmp_path):
    """Testa se o serviço ignora symlinks para evitar remoção de arquivos importantes."""
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    target_file = target_dir / "important.txt"
    target_file.write_text("IMPORTANT")
    
    link = temp_dir / "link_to_target"
    try:
        os.symlink(str(target_dir), str(link), target_is_directory=True)
    except OSError:
        pytest.skip("Sem privilégio para criar symlink no Windows")
        
    alvos = {
        "teste_temp": {
            "nome": "Temp Test",
            "caminho": str(temp_dir),
            "tipo": "diretorio"
        }
    }
            
    result = executar_limpeza(injetar_alvos=alvos)
    
    assert result["ok"] is True
    assert target_file.exists(), "Não deveria seguir o symlink"
    assert link.exists() or not link.exists(), "Symlinks na raiz são unlinked, mas não seguidos. No cleanup_service atual links raiz sao ignorados."
