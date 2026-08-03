import pytest
from modules.core import gpu_metrics
from modules.core.windows_command import CommandResult

def test_gpu_metrics_success(monkeypatch):
    def mock_run(*args, **kwargs):
        assert args[0][0] == "nvidia-smi"
        
        return CommandResult(
            ok=True,
            code="COMMAND_OK",
            returncode=0,
            stdout="0, NVIDIA GeForce RTX 3060, 15, 45, 1200, 12288\n1, NVIDIA GeForce RTX 4090, 5, 30, 500, 24576\n",
            stderr="",
            timed_out=False,
            cancelled=False,
            duration_ms=10,
            termination_ok=True
        )
        
    monkeypatch.setattr("modules.core.gpu_metrics.run_windows_command", mock_run)
    
    gpus = gpu_metrics.obter_metricas_gpu()
    
    assert len(gpus) == 2
    assert gpus[0]["id"] == "0"
    assert gpus[0]["nome"] == "NVIDIA GeForce RTX 3060"
    assert gpus[0]["uso_percentual"] == 15
    assert gpus[0]["temperatura_c"] == 45
    assert gpus[0]["vram_usada_mb"] == 1200
    assert gpus[0]["vram_total_mb"] == 12288

def test_gpu_metrics_failure(monkeypatch):
    def mock_run(*args, **kwargs):
        return CommandResult(
            ok=False,
            code="COMMAND_FAILED",
            returncode=1,
            stdout="",
            stderr="",
            timed_out=False,
            cancelled=False,
            duration_ms=10,
            termination_ok=True
        )
        
    monkeypatch.setattr("modules.core.gpu_metrics.run_windows_command", mock_run)
    
    gpus = gpu_metrics.obter_metricas_gpu()
    assert len(gpus) == 0

def test_gpu_metrics_timeout(monkeypatch):
    def mock_run(*args, **kwargs):
        return CommandResult(
            ok=False,
            code="COMMAND_TIMEOUT",
            returncode=None,
            stdout="",
            stderr="",
            timed_out=True,
            cancelled=False,
            duration_ms=2000,
            termination_ok=True
        )
        
    monkeypatch.setattr("modules.core.gpu_metrics.run_windows_command", mock_run)
    
    gpus = gpu_metrics.obter_metricas_gpu()
    assert len(gpus) == 0

def test_gpu_metrics_invalid_output(monkeypatch):
    def mock_run(*args, **kwargs):
        return CommandResult(
            ok=True,
            code="COMMAND_OK",
            returncode=0,
            stdout="invalid line here\nanother invalid\n0, GPU, NaN, 10, invalid, 100",
            stderr="",
            timed_out=False,
            cancelled=False,
            duration_ms=10,
            termination_ok=True
        )
        
    monkeypatch.setattr("modules.core.gpu_metrics.run_windows_command", mock_run)
    
    gpus = gpu_metrics.obter_metricas_gpu()
    
    assert len(gpus) == 1
    assert gpus[0]["uso_percentual"] == 0
    assert gpus[0]["vram_usada_mb"] == 0
    assert gpus[0]["temperatura_c"] == 10

