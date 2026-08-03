import pytest
from unittest.mock import patch, MagicMock
from modules import cli_app

@patch("modules.cli_app.Confirm.ask", return_value=False)
def test_fluxo_hardware_completo(mock_confirm):
    hw_info = {
        "sistema": {"os_nome": "Windows 11", "os_build": "22631"},
        "cpu": {"modelo": "Ryzen 7", "nucleos_fisicos": 8, "threads_logicas": 16, "frequencia_max_mhz": 4000},
        "memoria": {
            "total_instalada_gb": 32,
            "modulos": [{"slot": "DIMM 1", "capacidade_gb": 16, "velocidade_mhz": 3200}]
        },
        "gpus": [
            {"nome": "RTX 3060", "fabricante": "NVIDIA", "tipo": "dedicada", "vram_status": "exata", "vram_total_mb": 12288}
        ],
        "armazenamento": {
            "discos_fisicos": [{"modelo": "Samsung 980", "tipo_midia": "NVMe", "capacidade_gb": 1024}],
            "volumes": [{"unidade": "C:\\", "total_gb": 1024}]
        }
    }
    
    with patch("modules.cli_app.console.print") as mock_print:
        cli_app.fluxo_hardware_detalhado(hw_info)
        # Should not raise any KeyError and should print some info
        assert mock_print.called

@patch("modules.cli_app.Confirm.ask", return_value=False)
def test_fluxo_hardware_parcial_indisponiveis(mock_confirm):
    hw_info = {
        "sistema": {},
        "cpu": {},
        # Without memory, GPUs, etc. to simulate partial/failed fetch
    }
    with patch("modules.cli_app.console.print") as mock_print:
        cli_app.fluxo_hardware_detalhado(hw_info)
        assert mock_print.called

@patch("modules.cli_app.Confirm.ask", return_value=False)
def test_fluxo_hardware_gpu_ausente(mock_confirm):
    hw_info = {
        "cpu": {"modelo": "Core i3"},
        "memoria": {"total_instalada_gb": 8},
        "gpus": []
    }
    with patch("modules.cli_app.console.print") as mock_print:
        with patch("modules.cli_app.Panel") as mock_panel:
            cli_app.fluxo_hardware_detalhado(hw_info)
            assert any("Nenhuma GPU" in str(c) for c in mock_panel.call_args_list)

@patch("modules.cli_app.Confirm.ask", return_value=False)
def test_fluxo_hardware_multiplas_gpus(mock_confirm):
    hw_info = {
        "cpu": {"modelo": "Core i7"},
        "memoria": {"total_instalada_gb": 16},
        "gpus": [
            {"nome": "Intel UHD", "tipo": "integrada", "vram_status": "compartilhada"},
            {"nome": "RTX 3070", "tipo": "dedicada", "vram_status": "exata", "vram_total_mb": 8192}
        ]
    }
    with patch("modules.cli_app.console.print") as mock_print:
        cli_app.fluxo_hardware_detalhado(hw_info)
        assert mock_print.called
