import pytest
import json
from unittest.mock import patch, MagicMock
from modules.core import hardware_inventory
from modules.core.windows_command import CommandResult

def test_coletar_inventario_sucesso_completo():
    mock_raw = {
        "sistema": {
            "fabricante": "Lenovo",
            "modelo": "ThinkPad",
            "nome_dispositivo": "MY-PC",
            "os_nome": "Microsoft Windows 11 Pro",
            "os_versao": "10.0.26100",
            "os_build": "26100",
            "arquitetura": "64 bits",
            "placa_mae": {"fabricante": "Lenovo", "modelo": "21A1"},
            "bios": {"fabricante": "Lenovo", "versao": "R1ZET", "data": "2023-01-01"}
        },
        "cpu": {
            "modelo": "AMD Ryzen 7 PRO",
            "fabricante": "AuthenticAMD",
            "nucleos_fisicos": 8,
            "threads_logicas": 16,
            "frequencia_max_mhz": 2700,
            "arquitetura": 9
        },
        "memoria_modulos": [
            {"slot": "DIMM 0", "capacidade_bytes": 17179869184, "fabricante": "Samsung", "velocidade_mhz": 6400},
            {"slot": "DIMM 1", "capacidade_bytes": 17179869184, "fabricante": "Samsung", "velocidade_mhz": 6400}
        ],
        "gpus": [
            {"nome": "AMD Radeon(TM) Graphics", "fabricante": "Advanced Micro Devices", "vram_bytes": 536870912, "driver_versao": "31.0.12028.2"}
        ],
        "discos_fisicos": [
            {"modelo": "NVMe WD", "tipo_midia": 4, "barramento": 17, "capacidade_bytes": 1024209543168, "saude": "Healthy"}
        ],
        "volumes": [
            {"unidade": "C", "rotulo": "Windows", "tipo": 3, "total_bytes": 1000209543168, "livre_bytes": 500000000000}
        ]
    }
    
    mock_res = CommandResult(ok=True, code="SUCCESS", returncode=0, stdout=json.dumps(mock_raw), stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    with patch("modules.core.hardware_inventory.run_windows_command", return_value=mock_res):
        with patch("modules.core.hardware_inventory.psutil") as mock_psutil:
            mock_psutil.virtual_memory.return_value.total = 34359738368
            inv = hardware_inventory.coletar_inventario()
            
            assert inv["status"] == "completo"
            assert inv["sistema"]["modelo"] == "ThinkPad"
            assert inv["sistema"]["os_build"] == "26100"
            assert inv["cpu"]["modelo"] == "AMD Ryzen 7 PRO"
            assert inv["cpu"]["nucleos_fisicos"] == 8
            assert inv["cpu"]["arquitetura"] == "x64"
            
            assert inv["memoria"]["total_instalada_gb"] == 32.0
            assert len(inv["memoria"]["modulos"]) == 2
            
            assert len(inv["gpus"]) == 1
            assert inv["gpus"][0]["tipo"] == "integrada" # Radeon
            assert inv["gpus"][0]["vram_total_mb"] == 512
            assert inv["gpus"][0]["vram_status"] == "exata"
            
            assert inv["armazenamento"]["discos_fisicos"][0]["barramento"] == "NVMe"
            assert inv["armazenamento"]["discos_fisicos"][0]["tipo_midia"] == "NVMe"
            
            assert len(inv["armazenamento"]["volumes"]) == 1
            assert inv["armazenamento"]["volumes"][0]["unidade"] == "C:\\"
            assert inv["armazenamento"]["volumes"][0]["percentual_uso"] > 0

def test_coletar_inventario_gpu_dedicada_e_truncamento_vram():
    mock_raw = {
        "cpu": {"modelo": "Intel Core i9", "nucleos_fisicos": 8, "threads_logicas": 16},
        "gpus": [
            {"nome": "NVIDIA GeForce RTX 4090", "fabricante": "NVIDIA", "vram_bytes": 4294967295} # VRAM truncada comum em WMI 32-bit uint (-1)
        ]
    }
    mock_res = CommandResult(ok=True, code="SUCCESS", returncode=0, stdout=json.dumps(mock_raw), stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    with patch("modules.core.hardware_inventory.run_windows_command", return_value=mock_res):
        inv = hardware_inventory.coletar_inventario()
        assert inv["gpus"][0]["tipo"] == "dedicada"
        assert inv["gpus"][0]["vram_status"] == "estimada"
        assert inv["gpus"][0]["vram_total_mb"] is None

def test_coletar_inventario_fallback():
    mock_res = CommandResult(ok=False, code="ERROR", returncode=1, stdout="", stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    with patch("modules.core.hardware_inventory.run_windows_command", return_value=mock_res):
        with patch("modules.core.hardware_inventory.platform") as p:
            p.processor.return_value = "Fallback CPU"
            p.system.return_value = "Windows"
            p.release.return_value = "10"
            inv = hardware_inventory.coletar_inventario()
            
            assert inv["status"] == "parcial"
            assert inv["cpu"]["modelo"] == "Fallback CPU"
            assert inv["sistema"]["os_nome"] == "Windows 10"

def test_json_invalido():
    mock_res = CommandResult(ok=True, code="SUCCESS", returncode=0, stdout="{", stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    with patch("modules.core.hardware_inventory.run_windows_command", return_value=mock_res):
        inv = hardware_inventory.coletar_inventario()
        assert inv["status"] == "parcial"

def test_timeout():
    mock_res = CommandResult(ok=False, code='TIMEOUT', returncode=None, stdout='', stderr='', timed_out=True, cancelled=False, duration_ms=15000, termination_ok=True)
    with patch('modules.core.hardware_inventory.run_windows_command', return_value=mock_res):
        inv = hardware_inventory.coletar_inventario()
        assert inv['status'] == 'parcial'

def test_codigo_nao_zero():
    mock_res = CommandResult(ok=False, code='ERROR', returncode=1, stdout='', stderr='erro', timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    with patch('modules.core.hardware_inventory.run_windows_command', return_value=mock_res):
        inv = hardware_inventory.coletar_inventario()
        assert inv['status'] == 'parcial'

@pytest.mark.parametrize("gpu_nome, expected_tipo", [
    ("Intel Arc A770", "dedicada"),
    ("Intel(R) UHD Graphics 770", "integrada"),
    ("Intel Iris Xe Graphics", "integrada"),
    ("Intel HD Graphics 620", "integrada"),
    ("NVIDIA GeForce RTX 3060", "dedicada"),
    ("NVIDIA GTX 1650", "dedicada"),
    ("AMD Radeon RX 6700 XT", "dedicada"),
    ("AMD Radeon(TM) Graphics", "integrada"),
    ("AMD Radeon Graphics", "integrada"),
    ("Custom Unknown GPU", "desconhecida")
])
def test_coletar_inventario_gpu_tipos(gpu_nome, expected_tipo):
    mock_raw = {
        "cpu": {"modelo": "CPU"},
        "gpus": [
            {"nome": gpu_nome, "fabricante": "Unknown", "vram_bytes": 1024}
        ]
    }
    mock_res = CommandResult(ok=True, code="SUCCESS", returncode=0, stdout=json.dumps(mock_raw), stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    with patch("modules.core.hardware_inventory.run_windows_command", return_value=mock_res):
        inv = hardware_inventory.coletar_inventario()
        assert inv["gpus"][0]["tipo"] == expected_tipo
