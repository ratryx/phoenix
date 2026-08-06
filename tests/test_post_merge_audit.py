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
    
    if os.name == 'nt':
        app = obter_local_appdata()
        sys_dir = obter_windows_directory()
        
        # In actual Windows, the API should take precedence and not return the fake env vars,
        # unless it fails, but for CI we assume it succeeds.
        assert app != "C:\\PastaFalsaApp"
        assert sys_dir != "C:\\PastaFalsaSys"
    else:
        app = obter_local_appdata()
        sys_dir = obter_windows_directory()
        assert app == "C:\\PastaFalsaApp"
        assert sys_dir == "C:\\PastaFalsaSys"

def test_broken_symlink_junction_handling(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    
    broken_link = root / "broken"
    try:
        # Create a broken symlink
        os.symlink("does_not_exist", str(broken_link))
    except (OSError, AttributeError):
        pass # Not supported on this OS without admin

    if broken_link.exists(follow_symlinks=False):
        alvos = {
            "broken": {
                "nome": "Broken",
                "caminho": str(broken_link),
                "raiz_autorizada": str(root),
                "tipo": "diretorio"
            }
        }
        
        res = executar_limpeza(injetar_alvos=alvos)
        assert res["arquivos_total"] == 1
        assert res["arquivos_processados"] == 1
        assert res["arquivos_ignorados"] == 1
        assert res["parcial"] is True
        assert res["categorias"][0]["status"] in ("parcial", "falhou")

def test_root_identity_swap_mid_operation(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    
    alvos = {
        "swap": {
            "nome": "Swap",
            "caminho": str(root),
            "raiz_autorizada": str(root),
            "tipo": "diretorio"
        }
    }
    
    # We will monkeypatch _safe_scandir to throw RootChangedError as if identity changed
    def fake_safe_scandir(caminho, raiz_autorizada, cancel_event, root_val):
        raise RootChangedError("Raiz alterada durante a operação")
        
    with patch("modules.core.cleanup_service._safe_scandir", new=fake_safe_scandir):
        res = executar_limpeza(injetar_alvos=alvos)
        
        assert res["arquivos_total"] == 1
        assert res["arquivos_processados"] == 1
        assert res["arquivos_ignorados"] == 1
        assert res["arquivos_removidos"] == 0
        assert res["parcial"] is True
        
        # Check warnings do not contain absolute paths
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
