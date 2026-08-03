import sys
import pytest
from unittest.mock import patch, MagicMock
from modules.core.hardware_metrics import coletar_metricas_completas

def test_hardware_metrics_sem_gputil():
    # Simular ausência de GPUs ou falha no módulo gpu_metrics
    with patch("modules.core.gpu_metrics.obter_metricas_gpu", return_value=[]):
        res = coletar_metricas_completas()

        # Não deve crashear, gpus será vazia
        assert res["ok"] is True
        assert "cpu" in res
        assert "memoria" in res
        assert "disco" in res
        assert res["gpus"] == []

@patch("modules.core.hardware_metrics.psutil.disk_io_counters")
def test_hardware_metrics_falha_psutil_disco(mock_disk_io):
    # Simular exceção no disco
    mock_disk_io.side_effect = Exception("Disco inacessível")

    # Não deve crashear
    res = coletar_metricas_completas()
    assert res["ok"] is True

    # cpu e memória devem estar presentes
    assert "uso_percentual" in res["cpu"]
    assert "percentual_uso" in res["memoria"]

    # disco deve estar vazio porque as chaves só são adicionadas se read_mb e write_mb não forem None
    assert "leitura_mb_s" not in res["disco"]
    assert "escrita_mb_s" not in res["disco"]

@patch("modules.core.hardware_metrics.psutil.cpu_percent")
def test_hardware_metrics_falha_psutil_cpu(mock_cpu_percent):
    mock_cpu_percent.side_effect = Exception("CPU inacessível")

    res = coletar_metricas_completas()
    assert res["ok"] is True

    # cpu não deve ter uso_percentual devido ao tratamento de erro local retornar (None, None)
    assert "uso_percentual" not in res["cpu"]
    assert "uso_por_nucleo" not in res["cpu"]

    # Mas memória deve estar lá
    assert "percentual_uso" in res["memoria"]

@patch("modules.core.hardware_metrics.psutil.virtual_memory")
def test_hardware_metrics_falha_psutil_memoria(mock_virtual_memory):
    mock_virtual_memory.side_effect = Exception("RAM inacessível")

    res = coletar_metricas_completas()
    assert res["ok"] is True

    assert res["memoria"]["percentual_uso"] is None
    assert res["memoria"]["usada_gb"] is None
    assert res["memoria"]["disponivel_gb"] is None

    # cpu deve estar lá
    assert "uso_percentual" in res["cpu"]

from modules.core.hardware_metrics import obter_uso_cpu

def test_hardware_metrics_obter_uso_cpu_coletas():
    mock_psutil = MagicMock()

    # Primeira coleta
    mock_psutil.cpu_percent.return_value = [10.0, 30.0, 50.0, 10.0]
    total1, cores1 = obter_uso_cpu(mock_psutil)
    assert total1 == 25.0
    assert cores1 == [10.0, 30.0, 50.0, 10.0]
    mock_psutil.cpu_percent.assert_called_with(interval=0.1, percpu=True)

    # Coletas consecutivas
    mock_psutil.cpu_percent.return_value = [20.0, 20.0, 20.0, 20.0]
    total2, cores2 = obter_uso_cpu(mock_psutil)
    assert total2 == 20.0
    assert cores2 == [20.0, 20.0, 20.0, 20.0]

def test_hardware_metrics_obter_uso_cpu_clamp():
    mock_psutil = MagicMock()

    # Maior que 100
    mock_psutil.cpu_percent.return_value = [150.0, 200.0]
    total1, cores1 = obter_uso_cpu(mock_psutil)
    assert total1 == 100.0

    # Menor que 0
    mock_psutil.cpu_percent.return_value = [-10.0, -20.0]
    total2, cores2 = obter_uso_cpu(mock_psutil)
    assert total2 == 0.0

    # Valores inválidos, nulos, nans e lista vazia
    mock_psutil.cpu_percent.return_value = []
    total3, cores3 = obter_uso_cpu(mock_psutil)
    assert total3 is None
    assert cores3 is None

    import math
    mock_psutil.cpu_percent.return_value = ["150.0", None, float('nan'), -10, "abc"]
    total4, cores4 = obter_uso_cpu(mock_psutil)
    assert total4 == 50.0
    assert cores4 == [100.0, 0.0]
