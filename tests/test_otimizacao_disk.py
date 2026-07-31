import pytest
import time
from unittest.mock import patch
from modules.gui.jobs import JobManager
from modules.gui.api import PhoenixAPI
from modules.core.windows_command import CommandResult

def test_otimizacao_disk_sucesso():
    jm = JobManager(ttl_seconds=10)
    api = PhoenixAPI(hw_info={}, job_manager=jm)
    try:
        with patch("modules.otimizacao.run_windows_command") as mock_run:
            mock_run.return_value = CommandResult(
                ok=True, code="COMMAND_OK", returncode=0, stdout="TRIM completed.", stderr="",
                timed_out=False, cancelled=False, duration_ms=1000, termination_ok=True
            )
            
            res = api.otimizar_disco()
            job_id = res.get("job_id")
            assert job_id is not None
            
            # Polling helper
            start_time = time.time()
            status = {}
            while time.time() - start_time < 5.0:
                status = jm.consultar(job_id)
                if status["status"] == "done":
                    break
                time.sleep(0.05)
                
            assert status["status"] == "done"
            # disk success returns a dictionary; success includes bounded saida
            assert isinstance(status["resultado"], dict)
            assert status["resultado"]["ok"] is True
            assert status["resultado"]["codigo"] == "COMMAND_OK"
            assert status["resultado"]["saida"] == "TRIM completed."
            # runner timeout is exactly 270 seconds
            kwargs = mock_run.call_args[1]
            assert kwargs.get("timeout_seconds") == 270.0
    finally:
        jm.shutdown()

def test_otimizacao_disk_falha():
    jm = JobManager(ttl_seconds=10)
    api = PhoenixAPI(hw_info={}, job_manager=jm)
    try:
        with patch("modules.otimizacao.run_windows_command") as mock_run:
            # non-zero exit returns COMMAND_FAILED
            mock_run.return_value = CommandResult(
                ok=False, code="COMMAND_FAILED", returncode=1, stdout="", stderr="Access Denied",
                timed_out=False, cancelled=False, duration_ms=1000, termination_ok=True
            )
            
            res = api.otimizar_disco()
            job_id = res.get("job_id")
            
            start_time = time.time()
            status = {}
            while time.time() - start_time < 5.0:
                status = jm.consultar(job_id)
                if status["status"] == "done":
                    break
                time.sleep(0.05)
                
            assert status["status"] == "done"
            assert status["resultado"]["ok"] is False
            assert status["resultado"]["codigo"] == "COMMAND_FAILED"
            # stderr never crosses the public payload
            assert "Access Denied" not in str(status["resultado"])
            # success is not printed on failure
            assert "saida" not in status["resultado"]
    finally:
        jm.shutdown()

def test_otimizacao_disk_timeout():
    jm = JobManager(ttl_seconds=10)
    api = PhoenixAPI(hw_info={}, job_manager=jm)
    try:
        with patch("modules.otimizacao.run_windows_command") as mock_run:
            # timeout returns COMMAND_TIMEOUT
            mock_run.return_value = CommandResult(
                ok=False, code="COMMAND_TIMEOUT", returncode=None, stdout="", stderr="",
                timed_out=True, cancelled=False, duration_ms=270000, termination_ok=True
            )
            
            res = api.otimizar_disco()
            job_id = res.get("job_id")
            
            start_time = time.time()
            status = {}
            while time.time() - start_time < 5.0:
                status = jm.consultar(job_id)
                if status["status"] == "done":
                    break
                time.sleep(0.05)
                
            assert status["status"] == "done"
            # API timeout remains a truthful failed result
            assert status["resultado"]["ok"] is False
            assert status["resultado"]["codigo"] == "COMMAND_TIMEOUT"
    finally:
        jm.shutdown()

def test_otimizacao_disk_cancelado():
    jm = JobManager(ttl_seconds=10)
    api = PhoenixAPI(hw_info={}, job_manager=jm)
    try:
        with patch("modules.otimizacao.run_windows_command") as mock_run:
            # cancellation returns COMMAND_CANCELLED
            mock_run.return_value = CommandResult(
                ok=False, code="COMMAND_CANCELLED", returncode=None, stdout="", stderr="",
                timed_out=False, cancelled=True, duration_ms=1000, termination_ok=True
            )
            
            res = api.otimizar_disco()
            job_id = res.get("job_id")
            
            # Simulate api cancel call right after
            api.cancelar_tarefa(job_id)
            
            start_time = time.time()
            status = {}
            while time.time() - start_time < 5.0:
                status = jm.consultar(job_id)
                if status["status"] == "cancelled":
                    break
                time.sleep(0.05)
                
            # API cancellation ends cancelled
            assert status["status"] == "cancelled"
    finally:
        jm.shutdown()
