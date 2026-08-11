import pytest
from modules.driver_check import is_virtual_adapter, _classificar_driver, verificar_drivers_gpu
from unittest.mock import patch

def test_virtual_adapter_detection():
    assert is_virtual_adapter("Parsec Virtual Display Adapter", "Parsec Cloud Computer") is True
    assert is_virtual_adapter("Citrix Indirect Display Adapter", "Citrix Systems") is True
    assert is_virtual_adapter("NVIDIA GeForce RTX 4090", "NVIDIA") is False
    assert is_virtual_adapter("AMD Radeon RX 7900 XTX", "Advanced Micro Devices, Inc.") is False

def test_virtual_adapter_classification():
    # Deve ignorar a idade
    classificacao, cor, msg = _classificar_driver(500, "virtual")
    assert classificacao == "Adaptador virtual"
    assert "não avaliada" in msg

    classificacao, cor, msg = _classificar_driver(10, "virtual")
    assert classificacao == "Adaptador virtual"

def test_physical_adapter_classification():
    classificacao, _, _ = _classificar_driver(10, "fisico")
    assert classificacao == "Atualizado"

    classificacao, _, _ = _classificar_driver(400, "fisico")
    assert classificacao == "Desatualizado"

@patch("modules.driver_check._consultar_drivers_wmi")
@patch("modules.driver_check._consultar_versao_driver_nvidia")
def test_verificar_drivers_gpu_virtual_flow(mock_nvidia, mock_wmi):
    mock_wmi.return_value = [
        {
            "Name": "Parsec Virtual Display Adapter",
            "AdapterCompatibility": "Parsec",
            "DriverVersion": "1.0",
            "DriverDate": "20200101" # Muito antigo
        },
        {
            "Name": "NVIDIA GeForce GTX 1060",
            "AdapterCompatibility": "NVIDIA",
            "DriverVersion": "530.00",
            "DriverDate": "20230101" # Antigo
        }
    ]
    mock_nvidia.return_value = None

    resultados = verificar_drivers_gpu()
    assert len(resultados) == 2

    parsec = resultados[0]
    assert parsec["tipo_adaptador"] == "virtual"
    assert parsec["classificacao"] == "Adaptador virtual"

    nvidia = resultados[1]
    assert nvidia["tipo_adaptador"] == "fisico"
    assert nvidia["classificacao"] == "Desatualizado"
from modules.driver_check import executar_verificacao_drivers
from io import StringIO
from rich.console import Console

@patch("modules.driver_check.verificar_drivers_gpu")
def test_executar_verificacao_somente_virtual(mock_verificar):
    mock_verificar.return_value = [
        {"nome": "Parsec", "fabricante": "Parsec", "versao_driver": "1.0", "data_driver": "01/01/2020", "idade_dias": 1000, "tipo_adaptador": "virtual", "classificacao": "Adaptador virtual", "cor": "dim", "mensagem": "", "link_download": ""}
    ]

    with patch("modules.driver_check.console", Console(file=StringIO(), force_terminal=False)) as mock_console:
        executar_verificacao_drivers()
        output = mock_console.file.getvalue()

        assert "Nenhum driver físico de GPU requer revisão" in output
        assert "1 adaptador(es) virtual(is) não foram avaliados" in output

@patch("modules.driver_check.verificar_drivers_gpu")
def test_executar_verificacao_fisico_atualizado_e_virtual(mock_verificar):
    mock_verificar.return_value = [
        {"nome": "Parsec", "fabricante": "Parsec", "versao_driver": "1.0", "data_driver": "01/01/2020", "idade_dias": 1000, "tipo_adaptador": "virtual", "classificacao": "Adaptador virtual", "cor": "dim", "mensagem": "", "link_download": ""},
        {"nome": "NVIDIA", "fabricante": "NVIDIA", "versao_driver": "1.0", "data_driver": "01/01/2020", "idade_dias": 10, "tipo_adaptador": "fisico", "classificacao": "Atualizado", "cor": "green", "mensagem": "", "link_download": ""}
    ]

    with patch("modules.driver_check.console", Console(file=StringIO(), force_terminal=False)) as mock_console:
        executar_verificacao_drivers()
        output = mock_console.file.getvalue()

        assert "Nenhum driver físico de GPU requer revisão" in output
        assert "1 adaptador(es) virtual(is) não foram avaliados" in output

@patch("modules.driver_check.verificar_drivers_gpu")
def test_executar_verificacao_fisico_desatualizado_e_virtual(mock_verificar):
    mock_verificar.return_value = [
        {"nome": "Parsec", "fabricante": "Parsec", "versao_driver": "1.0", "data_driver": "01/01/2020", "idade_dias": 1000, "tipo_adaptador": "virtual", "classificacao": "Adaptador virtual", "cor": "dim", "mensagem": "", "link_download": ""},
        {"nome": "NVIDIA", "fabricante": "NVIDIA", "versao_driver": "1.0", "data_driver": "01/01/2020", "idade_dias": 1000, "tipo_adaptador": "fisico", "classificacao": "Desatualizado", "cor": "red", "mensagem": "", "link_download": ""}
    ]

    with patch("modules.driver_check.console", Console(file=StringIO(), force_terminal=False)) as mock_console:
        executar_verificacao_drivers()
        output = mock_console.file.getvalue()

        assert "1 driver(s) desatualizado(s) detectado(s)" in output
        assert "1 adaptador(es) virtual(is) não foram avaliados" in output
