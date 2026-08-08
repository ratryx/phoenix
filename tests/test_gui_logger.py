import pytest
from unittest.mock import patch, MagicMock
from modules.core.gui_logger import GUILogger

@pytest.fixture(autouse=True)
def reset_gui_logger():
    yield
    GUILogger.shutdown()

def test_gui_logger_setup_shutdown():
    GUILogger.setup()
    assert GUILogger._instance is not None
    GUILogger.shutdown()
    assert GUILogger._instance is None
    assert GUILogger._progress is None
    assert len(GUILogger._tasks) == 0

def test_gui_logger_progress_lifecycle():
    GUILogger.setup()
    GUILogger.log_job_progress('job123', 50, 'Carregando')
    assert GUILogger._progress is not None
    assert 'job123' in GUILogger._tasks
    job_info = {'status': 'done', 'operation_name': 'rotina_completa'}
    GUILogger.log_job_terminal_state('job123', job_info)
    assert 'job123' not in GUILogger._tasks
    assert GUILogger._progress is None

def test_gui_logger_multiple_tasks():
    GUILogger.setup()
    GUILogger.log_job_progress('task1', 10, 'Init 1')
    GUILogger.log_job_progress('task2', 20, 'Init 2')
    assert len(GUILogger._tasks) == 2
    job_info = {'status': 'failed', 'resultado': {'codigo': 'ERRO_TESTE'}}
    GUILogger.log_job_terminal_state('task1', job_info)
    assert len(GUILogger._tasks) == 1
    assert GUILogger._progress is not None
    GUILogger.log_job_terminal_state('task2', {'status': 'cancelled'})
    assert len(GUILogger._tasks) == 0
    assert GUILogger._progress is None
