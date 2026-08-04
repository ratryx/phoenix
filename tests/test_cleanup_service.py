import os
import stat
import threading
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from modules.core.cleanup_service import executar_limpeza, _is_reparse_point, is_safe_path, _remover_arquivo, _remover_diretorio_recursivo
from modules.core.exceptions import JobCancelledError

def test_executar_limpeza_basic(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    file1 = temp_dir / "file1.txt"
    file1.write_text("Hello World!")

    alvos = {
        "teste_temp": {
            "nome": "Temp Test",
            "caminho": str(temp_dir),
            "raiz_autorizada": str(temp_dir),
            "tipo": "diretorio"
        }
    }

    result = executar_limpeza(injetar_alvos=alvos)
    assert result["ok"] is True
    assert result["arquivos_removidos"] == 1
    assert result["arquivos_ignorados"] == 0
    assert result["espaco_liberado_bytes"] == 12
    assert not file1.exists()

def test_executar_limpeza_cancel_before_unlink(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    file1 = temp_dir / "f1.txt"
    file1.write_text("123")

    alvos = {
        "t": {
            "nome": "T",
            "caminho": str(temp_dir),
            "raiz_autorizada": str(temp_dir),
            "tipo": "diretorio"
        }
    }

    cancel_event = threading.Event()
    call_count = 0
    original_lstat = os.lstat

    def side_effect_lstat(path):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            cancel_event.set()
        return original_lstat(path)

    with patch("os.lstat", side_effect=side_effect_lstat):
        with pytest.raises(JobCancelledError):
            executar_limpeza(cancel_event=cancel_event, injetar_alvos=alvos)

    assert file1.exists(), "File should not be deleted if cancelled right before unlink"

def test_executar_limpeza_cancel_mid_recursion(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    for i in range(5):
        (temp_dir / f"{i}.txt").write_text("ok")

    alvos = {
        "t": {
            "nome": "T",
            "caminho": str(temp_dir),
            "raiz_autorizada": str(temp_dir),
            "tipo": "diretorio"
        }
    }
    cancel_event = threading.Event()

    original_unlink = Path.unlink
    unlink_count = 0
    def fake_unlink(self):
        nonlocal unlink_count
        unlink_count += 1
        if unlink_count == 3:
            cancel_event.set()
        original_unlink(self)

    with patch("pathlib.Path.unlink", new=fake_unlink):
        with pytest.raises(JobCancelledError):
            executar_limpeza(cancel_event=cancel_event, injetar_alvos=alvos)

    remnants = list(temp_dir.iterdir())
    assert len(remnants) == 2, "Should have 2 files left after 3 removed and cancelled"

def test_temp_vs_temp2():
    assert not is_safe_path("C:\\Users\\Bob\\AppData\\Local\\Temp2\\file.txt", "C:\\Users\\Bob\\AppData\\Local\\Temp")
    assert is_safe_path("C:\\Users\\Bob\\AppData\\Local\\Temp\\file.txt", "C:\\Users\\Bob\\AppData\\Local\\Temp")

def test_escape_dotdot():
    assert not is_safe_path("C:\\Windows\\Temp\\..\\System32\\cmd.exe", "C:\\Windows\\Temp")

def test_unauthorized_root(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    alvos = {
        "t": {
            "nome": "T",
            "caminho": str(temp_dir),
            "tipo": "diretorio"
        }
    }
    with pytest.raises(ValueError, match="sem raiz_autorizada"):
        executar_limpeza(injetar_alvos=alvos)

def test_root_symlink_junction(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    link_dir = tmp_path / "link"
    try:
        os.symlink(str(temp_dir), str(link_dir), target_is_directory=True)
    except OSError:
        pytest.skip("No symlink privilege")

    alvos = {
        "t": {
            "nome": "T",
            "caminho": str(link_dir),
            "raiz_autorizada": str(link_dir),
            "tipo": "diretorio"
        }
    }
    result = executar_limpeza(injetar_alvos=alvos)
    assert result["arquivos_removidos"] == 0

def test_item_swapped_reparse_point(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    file1 = temp_dir / "f1.txt"
    file1.write_text("abc")

    alvos = {
        "t": {
            "nome": "T",
            "caminho": str(temp_dir),
            "raiz_autorizada": str(temp_dir),
            "tipo": "diretorio"
        }
    }

    call_count = 0
    original_lstat = os.lstat

    def fake_lstat(path):
        st = original_lstat(path)
        if "f1.txt" in str(path):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                class FakeStat:
                    st_mode = st.st_mode
                    st_ino = st.st_ino
                    st_dev = st.st_dev
                    st_size = st.st_size
                    st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT
                return FakeStat()
        return st

    with patch("os.lstat", side_effect=fake_lstat):
        result = executar_limpeza(injetar_alvos=alvos)

    assert file1.exists()
    assert result["arquivos_ignorados"] == 1
    assert result["arquivos_removidos"] == 0

def test_permission_error_iterdir(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    alvos = {
        "t": {
            "nome": "T",
            "caminho": str(temp_dir),
            "raiz_autorizada": str(temp_dir),
            "tipo": "diretorio"
        }
    }

    def fake_scandir(*args, **kwargs):
        raise PermissionError("Access Denied")

    with patch("os.scandir", new=fake_scandir):
        result = executar_limpeza(injetar_alvos=alvos)

    assert result["arquivos_ignorados"] == 1
    assert result["categorias"][0]["status"] in ("parcial", "falhou")
    assert "PermissionError" in result["avisos"][0]
    assert result["parcial"] is True

def test_no_false_complete_category(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    file1 = temp_dir / "f1.txt"
    file1.write_text("123")

    alvos = {
        "t": {
            "nome": "T",
            "caminho": str(temp_dir),
            "raiz_autorizada": str(temp_dir),
            "tipo": "diretorio"
        }
    }

    def fake_unlink(self):
        raise PermissionError("Denied")

    with patch("pathlib.Path.unlink", new=fake_unlink):
        result = executar_limpeza(injetar_alvos=alvos)

    assert result["arquivos_ignorados"] == 1
    assert result["categorias"][0]["status"] == "parcial"
    assert result["parcial"] is True
    assert result["espaco_liberado_bytes"] == 0

def test_bytes_only_after_removal(tmp_path):
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    file1 = temp_dir / "f1.txt"
    file1.write_text("abcdef")

    alvos = {
        "t": {
            "nome": "T",
            "caminho": str(temp_dir),
            "raiz_autorizada": str(temp_dir),
            "tipo": "diretorio"
        }
    }

    def fake_unlink(self):
        raise PermissionError("Denied")

    with patch("pathlib.Path.unlink", new=fake_unlink):
        result = executar_limpeza(injetar_alvos=alvos)

    assert result["espaco_liberado_bytes"] == 0
    assert file1.exists()
