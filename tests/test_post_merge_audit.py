import os
import json
import time
from pathlib import Path
from unittest.mock import patch
import threading
from dataclasses import dataclass

from modules.core.windows_known_folders import obter_local_appdata, obter_windows_directory
from modules.core.cleanup_service import _validar_raiz, _enumerar_seguro, executar_limpeza, RootChangedError, RootValidation
from modules.gui.jobs import JobManager
from modules.core.exceptions import JobCancelledError

def test_windows_known_folders_adulterated(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", "C:\\PastaFalsaApp")
    monkeypatch.setenv("SystemRoot", "C:\\PastaFalsaSys")
    monkeypatch.setattr(os, "name", "nt")

    # Mock SHGetKnownFolderPath to fail (return != 0)
    def fake_SHGetKnownFolderPath(*args):
        return -1 # error

    # Mock GetWindowsDirectoryW to fail (return 0)
    def fake_GetWindowsDirectoryW(*args):
        return 0

    with patch("ctypes.windll.shell32.SHGetKnownFolderPath", side_effect=fake_SHGetKnownFolderPath, create=True):
        app = obter_local_appdata()
        # In Windows, if API fails, it should return "" and NOT fallback to LOCALAPPDATA
        assert app == ""

    with patch("ctypes.windll.kernel32.GetWindowsDirectoryW", side_effect=fake_GetWindowsDirectoryW, create=True):
        sys_dir = obter_windows_directory()
        assert sys_dir == ""

def test_broken_symlink_junction_handling(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()

    broken_link = root / "broken"
    valid_link = root / "valid"
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    # Tentaremos criar uma junction real no Windows usando mklink /J
    # Se falhar (ex: sem privilégios ou erro), mockamos a funcionalidade.
    real_junctions_created = False
    if os.name == 'nt':
        import subprocess
        # Cria uma junction válida
        res1 = subprocess.run(["cmd", "/c", "mklink", "/J", str(valid_link), str(target_dir)], capture_output=True)

        # Cria uma junction quebrada (apontando para algo que não existe)
        res2 = subprocess.run(["cmd", "/c", "mklink", "/J", str(broken_link), str(tmp_path / "does_not_exist")], capture_output=True)

        if res1.returncode == 0 and res2.returncode == 0:
            real_junctions_created = True

    if not real_junctions_created:
        # Fallback para Mocks
        broken_link.mkdir() # we create a real dir so it can be scanned
        valid_link.mkdir()

        # Monkeypatch Path.is_junction
        original_is_junction = Path.is_junction if hasattr(Path, 'is_junction') else lambda self: False
        def fake_is_junction(self):
            if self.name in ("broken", "valid"):
                return True
            return original_is_junction(self)

        if hasattr(Path, 'is_junction'):
            monkeypatch.setattr(Path, "is_junction", fake_is_junction)
        else:
            monkeypatch.setattr(Path, "is_symlink", fake_is_junction) # fallback pra symlink

        import stat
        original_lstat = os.lstat
        def fake_lstat(path, *args, **kwargs):
            st = original_lstat(path, *args, **kwargs)
            if Path(path).name in ("broken", "valid"):
                class FakeStat:
                    def __init__(self, base_st):
                        self.st_dev = base_st.st_dev
                        self.st_ino = base_st.st_ino
                        self.st_mode = base_st.st_mode
                        self.st_size = base_st.st_size
                        self.st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT
                return FakeStat(st)
            return st
        monkeypatch.setattr(os, "lstat", fake_lstat)

    alvos = {
        "links": {
            "nome": "Links",
            "caminho": str(root),
            "raiz_autorizada": str(root),
            "tipo": "diretorio"
        }
    }

    with patch("pathlib.Path.unlink") as mock_unlink, patch("pathlib.Path.rmdir") as mock_rmdir:
        res = executar_limpeza(injetar_alvos=alvos)

        # As junctions nunca devem ser seguidas ou removidas
        # Total = 1 (a raiz) + 2 (os itens dentro dela: broken, valid)
        assert mock_unlink.call_count == 0
        assert mock_rmdir.call_count == 0

        # O resultado deve marcar ignorados
        assert res["arquivos_processados"] >= 2
        assert res["arquivos_ignorados"] >= 2

def test_root_identity_swap_mid_operation(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "file.txt").touch()
    
    alvos = {
        "swap": {
            "nome": "Swap",
            "caminho": str(root),
            "raiz_autorizada": str(root),
            "tipo": "diretorio"
        }
    }

    original_lstat = os.lstat
    
    class FakeStat:
        def __init__(self, ino):
            st = original_lstat(str(root))
            self.st_ino = ino
            self.st_dev = st.st_dev
            self.st_mode = st.st_mode
            self.st_file_attributes = getattr(st, 'st_file_attributes', 0)
    
    import inspect
    def fake_lstat(path, *args, **kwargs):
        if path == str(root):
            stack = inspect.stack()
            for frame_info in stack:
                if frame_info.function == "_processar_alvo":
                    if any(f.function == "_revalidar" for f in stack):
                        return FakeStat(200)
                    return FakeStat(100)
            return FakeStat(100) # Normal identity for counting phase
        return original_lstat(path, *args, **kwargs)
        
    with patch("os.lstat", side_effect=fake_lstat), \
         patch("pathlib.Path.unlink") as mock_unlink, \
         patch("pathlib.Path.rmdir") as mock_rmdir:
         
        res = executar_limpeza(injetar_alvos=alvos)
        
        assert mock_unlink.call_count == 0
        assert mock_rmdir.call_count == 0
        
        assert res["arquivos_total"] == 1
        assert res["arquivos_processados"] == 1
        assert res["arquivos_ignorados"] == 1
        assert res["arquivos_removidos"] == 0
        assert res["parcial"] is True
        
        warning_str = str(res["avisos"])
        assert str(root) not in warning_str
        assert "Raiz alterada durante a operação" in warning_str

def test_json_dumps_runtime_error_monkeypatch():
    cb_calls = []
    def term_cb(job_id, job):
        cb_calls.append((job_id, job["status"], job["resultado"]))

    jm = JobManager(watchdog_interval=0.1, on_terminal_state=term_cb)

    def operacao():
        return {"data": 42}

    def wait_for_worker_exit(jm, job_id, timeout=2.0):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            with jm._lock:
                job = jm._jobs.get(job_id)
                if not job or not job["worker_alive"]:
                    return
            time.sleep(0.01)

    with patch("json.dumps", side_effect=RuntimeError("Simulated RuntimeError in JSON dumps")):
        job_id = jm.submit(operacao, exclusive_group="json_group")
        wait_for_worker_exit(jm, job_id)

    status = jm.consultar(job_id)
    assert status["status"] == "failed"
    assert status["resultado"]["codigo"] == "JOB_RESULT_INVALID"

    with jm._lock:
        job_internal = jm._jobs[job_id]
        assert job_internal["worker_alive"] is False
        assert job_internal["completed_at"] is not None

    assert len(cb_calls) == 1
    assert cb_calls[0][1] == "failed"

    assert jm._exclusive_groups.get("json_group") is None
    jm.shutdown()
