import pytest
from modules.core import gpu_metrics
from modules.core.windows_command import CommandResult

def test_gpu_metrics_success(monkeypatch):
    def mock_run(*args, **kwargs):
        # verifica comando ausente/invalido (comando e timeout enviados corretamente)
        assert args[0][0] == "nvidia-smi"
        assert kwargs.get("timeout_seconds") == 2.0
        
        return CommandResult(
            ok=True,
            code="COMMAND_OK",
            returncode=0,
            # uma GPU e múltiplas GPUs; 
            stdout=(
                "0, NVIDIA GeForce RTX 3060, 15, 45, 1200, 12288\n"
                "1, NVIDIA GeForce RTX 4090, 5, 30, 500, 24576\n"
            ),
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
            stdout=(
                "invalid line here\n"
                "another invalid\n"
                # N/A, [N/A], NaN, infinito, texto inválido
                "0, GPU 1, N/A, [N/A], NaN, INF\n"
                "1, GPU 2, texto, Not Supported, -INF, +INF\n"
                # zeros reais, valores negativos, etc.
                "2, GPU 3, 0, 0, 0, 0\n"
                "3, GPU 4, -10, -5, -1, -500\n"
            ),
            stderr="",
            timed_out=False,
            cancelled=False,
            duration_ms=10,
            termination_ok=True
        )
        
    monkeypatch.setattr("modules.core.gpu_metrics.run_windows_command", mock_run)
    
    gpus = gpu_metrics.obter_metricas_gpu()
    
    assert len(gpus) == 4
    
    # N/A, [N/A], NaN, infinito
    assert gpus[0]["uso_percentual"] is None
    assert gpus[0]["temperatura_c"] is None
    assert gpus[0]["vram_usada_mb"] is None
    assert gpus[0]["vram_total_mb"] is None
    
    # texto, Not Supported, -INF, +INF
    assert gpus[1]["uso_percentual"] is None
    assert gpus[1]["temperatura_c"] is None
    assert gpus[1]["vram_usada_mb"] is None
    assert gpus[1]["vram_total_mb"] is None
    
    # zeros reais (vram_total > 0 para ser valido, entao vram_total=0 eh None)
    assert gpus[2]["uso_percentual"] == 0
    assert gpus[2]["temperatura_c"] == 0
    assert gpus[2]["vram_usada_mb"] == 0
    assert gpus[2]["vram_total_mb"] is None # total ram <= 0 is invalid
    
    # valores negativos
    assert gpus[3]["uso_percentual"] is None
    assert gpus[3]["temperatura_c"] is None
    assert gpus[3]["vram_usada_mb"] is None
    assert gpus[3]["vram_total_mb"] is None

def test_gpu_metrics_command_ausente(monkeypatch):
    def mock_run(*args, **kwargs):
        return CommandResult(
            ok=False,
            code="COMMAND_NOT_FOUND",
            returncode=None,
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
