import pytest
from unittest.mock import patch, MagicMock
from modules.gui.api import PhoenixAPI
from modules.gui.jobs import JobManager
import time

def test_api_restore_point_cancellation():
    jm = JobManager(ttl_seconds=10)
    api = PhoenixAPI(hw_info={}, job_manager=jm)
    
    with patch("modules.otimizacao.run_windows_command") as mock_run:
        with patch("modules.otimizacao.is_admin", return_value=True):
            from modules.core.windows_command import CommandResult
            mock_run.return_value = CommandResult(
                ok=False, code="COMMAND_CANCELLED", returncode=None, stdout="", stderr="",
                timed_out=False, cancelled=True, duration_ms=10, termination_ok=True
            )
            
            # Start restore point job
            res = api.criar_ponto_restauracao()
            job_id = res.get("job_id")
            assert job_id is not None
            
            # Cancel job
            api.cancelar_tarefa(job_id)
            
            # Wait a bit for threads
            time.sleep(0.1)
            
            status = jm.consultar(job_id)
            assert status["status"] == "cancelled"
