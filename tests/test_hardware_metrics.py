import pytest
import sys
from unittest.mock import patch, MagicMock
from modules.core import hardware_metrics

def test_coletar_metricas_completas():
    with patch("modules.core.hardware_metrics.psutil") as mock_psutil:
        mock_psutil.cpu_freq.return_value.current = 2400
        
        mock_cpu_pct = MagicMock()
        mock_cpu_pct.side_effect = [50, [50, 60, 40, 70]] # por nucleo
        mock_psutil.cpu_percent = mock_cpu_pct
        
        mock_psutil.virtual_memory.return_value.percent = 45.0
        mock_psutil.virtual_memory.return_value.used = 8589934592
        mock_psutil.virtual_memory.return_value.available = 8589934592
        
        mock_gputil = MagicMock()
        mock_gpu = MagicMock()
        mock_gpu.id = 0
        mock_gpu.name = "NVIDIA"
        mock_gpu.load = 0.99
        mock_gpu.temperature = 80
        mock_gpu.memoryUsed = 2048
        mock_gpu.memoryTotal = 8192
        mock_gputil.getGPUs.return_value = [mock_gpu]

        with patch("modules.core.hardware_metrics._get_disk_io_stateful", return_value=(100.5, 50.2)):
            with patch.dict(sys.modules, {'GPUtil': mock_gputil}):
                metrics = hardware_metrics.coletar_metricas_completas()
                
                assert metrics["cpu"]["uso_percentual"] == 50
                assert metrics["cpu"]["frequencia_atual_mhz"] == 2400
                assert metrics["memoria"]["percentual_uso"] == 45.0
                assert metrics["memoria"]["usada_gb"] == 8.0
                assert metrics["memoria"]["disponivel_gb"] == 8.0
                assert metrics["disco"]["leitura_mb_s"] == 100.5
                assert metrics["disco"]["escrita_mb_s"] == 50.2
                assert len(metrics["gpus"]) == 1
                assert metrics["gpus"][0]["nome"] == "NVIDIA"
                assert metrics["gpus"][0]["uso_percentual"] == 99

def test_disk_io_stateful():
    with patch("modules.core.hardware_metrics.psutil") as mock_psutil:
        mock_counters1 = MagicMock()
        mock_counters1.read_bytes = 1048576 * 10
        mock_counters1.write_bytes = 1048576 * 5
        
        mock_counters2 = MagicMock()
        mock_counters2.read_bytes = 1048576 * 30 # +20MB
        mock_counters2.write_bytes = 1048576 * 15 # +10MB
        
        mock_psutil.disk_io_counters.side_effect = [mock_counters1, mock_counters2]
        
        # Reset do estado global
        hardware_metrics.reset_io_counters()
        hardware_metrics._last_io_time = 0
        
        with patch("modules.core.hardware_metrics.time") as mock_time:
            mock_time.monotonic.return_value = 100.0
            r, w = hardware_metrics._get_disk_io_stateful()
            assert r == 0.0
            assert w == 0.0
            
            # Simulando tick seguinte (tempo e bytes maiores)
            mock_time.monotonic.return_value = 101.0
            
            r, w = hardware_metrics._get_disk_io_stateful()
            assert r == 20.0
            assert w == 10.0
