import pytest
from modules.hardware import classificar_capacidade_hardware

def test_hardware_classification_no_gpu():
    hw = {
        "cpu": {"threads_logicas": 4},
        "memoria": {"total_instalada_gb": 8},
        "gpus": []
    }
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_rtx_estimada_none():
    hw = {
        "cpu": {"threads_logicas": 4},
        "memoria": {"total_instalada_gb": 8},
        "gpus": [
            {
                "nome": "NVIDIA GeForce RTX 3060",
                "tipo": "dedicada",
                "vram_status": "estimada",
                "vram_total_mb": None
            }
        ]
    }
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_nvidia_exata():
    hw = {
        "cpu": {"threads_logicas": 4},
        "memoria": {"total_instalada_gb": 8},
        "gpus": [
            {
                "nome": "NVIDIA GeForce GTX 1650",
                "tipo": "dedicada",
                "vram_status": "exata",
                "vram_total_mb": 4096
            }
        ]
    }
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_intel_uhd_integrada():
    hw = {
        "cpu": {"threads_logicas": 8},
        "memoria": {"total_instalada_gb": 16},
        "gpus": [
            {
                "nome": "Intel(R) UHD Graphics",
                "tipo": "integrada",
                "vram_status": "compartilhada",
                "vram_total_mb": 128
            }
        ]
    }
    # 8 threads = 2 pts, 16GB = 2 pts => total = 4 (alto) sem GPU dedicada
    assert classificar_capacidade_hardware(hw) == "alto"

def test_hardware_classification_intel_arc_dedicada():
    hw = {
        "cpu": {"threads_logicas": 4},
        "memoria": {"total_instalada_gb": 8},
        "gpus": [
            {
                "nome": "Intel Arc A770",
                "tipo": "dedicada",
                "vram_status": "exata",
                "vram_total_mb": 8192
            }
        ]
    }
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_amd_radeon_integrada():
    hw = {
        "cpu": {"threads_logicas": 4},
        "memoria": {"total_instalada_gb": 8},
        "gpus": [
            {
                "nome": "AMD Radeon(TM) Graphics",
                "tipo": "integrada",
                "vram_status": "compartilhada",
                "vram_total_mb": 512
            }
        ]
    }
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_amd_rx_dedicada():
    hw = {
        "cpu": {"threads_logicas": 4},
        "memoria": {"total_instalada_gb": 8},
        "gpus": [
            {
                "nome": "AMD Radeon RX 6600",
                "tipo": "dedicada",
                "vram_status": "exata",
                "vram_total_mb": 8192
            }
        ]
    }
    assert classificar_capacidade_hardware(hw) == "medio"
