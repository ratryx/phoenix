import pytest
import os
import json
from unittest.mock import patch
from modules.core import hardware_cache

def test_cache_ciclo_completo(tmp_path):
    with patch("modules.core.hardware_cache.CACHE_FILE", tmp_path / "hardware.json"):
        hardware_cache.deletar_cache()
        
        cache_vazio = hardware_cache.carregar_cache_estatico()
        assert cache_vazio is None
        
        fake_hw = {
            "schema_version": 2,
            "status": "completo",
            "coletado_em": "2023-01-01T00:00:00.000",
            "cpu": {"modelo": "Test CPU"}
        }
        
        res = hardware_cache.salvar_cache_estatico(fake_hw)
        assert res is True
        
        cache_lido = hardware_cache.carregar_cache_estatico()
        assert cache_lido is not None
        assert cache_lido["cpu"]["modelo"] == "Test CPU"
        
        hardware_cache.deletar_cache()
        assert hardware_cache.carregar_cache_estatico() is None

def test_cache_ignora_metricas_dinamicas(tmp_path):
    with patch("modules.core.hardware_cache.CACHE_FILE", tmp_path / "hardware.json"):
        fake_hw = {
            "schema_version": 2,
            "status": "completo",
            "cpu": {"modelo": "Test CPU", "uso_percentual": 55},
            "gpus": [
                {"nome": "Test GPU", "uso_percentual": 99, "temperatura_c": 80}
            ]
        }
        
        with pytest.raises(ValueError, match="Tentativa de salvar métricas dinâmicas no cache"):
            hardware_cache.salvar_cache_estatico(fake_hw)

def test_cache_rejeita_v1(tmp_path):
    with patch("modules.core.hardware_cache.CACHE_FILE", tmp_path / "hardware.json"):
        # Simula arquivo antigo v1
        c_file = tmp_path / "hardware.json"
        c_file.write_text(json.dumps({
            "schema_version": 1,
            "cpu": {"modelo": "V1 CPU"}
        }), encoding="utf-8")
        
        cache_lido = hardware_cache.carregar_cache_estatico()
        assert cache_lido is None # Cache descartado pois schema_version < 2
