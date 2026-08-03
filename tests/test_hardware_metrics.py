import sys
import pytest
from unittest.mock import patch, MagicMock
from modules.core.hardware_metrics import coletar_metricas_completas

def test_hardware_metrics_sem_gputil():
    # Simular a ausência do GPUtil
    with patch.dict(sys.modules, {'GPUtil': None}):
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

    # cpu não tem uso_percentual
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
