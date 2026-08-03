import pytest
from modules.hardware import classificar_capacidade_hardware

# Base base: 1 pt (CPU) + 0 pts (RAM) = 1 pt (baixo)
def get_base_hw():
    return {
        "cpu": {"threads_logicas": 4},        # 1 pt
        "memoria": {"total_instalada_gb": 4}, # 0 pt
        "gpus": []
    }

def test_hardware_classification_no_gpu():
    hw = get_base_hw()
    assert classificar_capacidade_hardware(hw) == "baixo"

def test_hardware_classification_rtx_estimada_none():
    hw = get_base_hw()
    hw["gpus"].append({
        "nome": "NVIDIA GeForce RTX 3060",
        "tipo": "dedicada",
        "vram_status": "estimada",
        "vram_total_mb": None
    })
    # GPU dedicada (estimada ok) = +1 pt => 2 pts (medio)
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_nvidia_exata():
    hw = get_base_hw()
    hw["gpus"].append({
        "nome": "NVIDIA GeForce GTX 1650",
        "tipo": "dedicada",
        "vram_status": "exata",
        "vram_total_mb": 4096
    })
    # GPU dedicada (exata >= 1024) = +1 pt => 2 pts (medio)
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_intel_arc_dedicada():
    hw = get_base_hw()
    hw["gpus"].append({
        "nome": "Intel Arc A770",
        "tipo": "dedicada",
        "vram_status": "exata",
        "vram_total_mb": 8192
    })
    # GPU dedicada (exata >= 1024) = +1 pt => 2 pts (medio)
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_amd_rx_dedicada():
    hw = get_base_hw()
    hw["gpus"].append({
        "nome": "AMD Radeon RX 6600",
        "tipo": "dedicada",
        "vram_status": "exata",
        "vram_total_mb": 8192
    })
    # GPU dedicada = +1 pt => 2 pts (medio)
    assert classificar_capacidade_hardware(hw) == "medio"

def test_hardware_classification_intel_uhd_integrada():
    hw = get_base_hw()
    hw["gpus"].append({
        "nome": "Intel(R) UHD Graphics",
        "tipo": "integrada",
        "vram_status": "compartilhada",
        "vram_total_mb": 128
    })
    # GPU integrada não pontua => 1 pt (baixo)
    assert classificar_capacidade_hardware(hw) == "baixo"

def test_hardware_classification_amd_radeon_integrada():
    hw = get_base_hw()
    hw["gpus"].append({
        "nome": "AMD Radeon(TM) Graphics",
        "tipo": "integrada",
        "vram_status": "compartilhada",
        "vram_total_mb": 512
    })
    # GPU integrada não pontua => 1 pt (baixo)
    assert classificar_capacidade_hardware(hw) == "baixo"

def test_hardware_classification_gpu_desconhecida():
    hw = get_base_hw()
    hw["gpus"].append({
        "nome": "Placa genérica",
        "tipo": "desconhecida",
        "vram_status": "indisponivel",
        "vram_total_mb": None
    })
    # GPU desconhecida não pontua => 1 pt (baixo)
    assert classificar_capacidade_hardware(hw) == "baixo"

def test_hardware_classification_vram_abaixo_1024():
    hw = get_base_hw()
    hw["gpus"].append({
        "nome": "NVIDIA GeForce GT 710",
        "tipo": "dedicada",
        "vram_status": "exata",
        "vram_total_mb": 512
    })
    # GPU dedicada mas vram < 1024 não pontua => 1 pt (baixo)
    assert classificar_capacidade_hardware(hw) == "baixo"
