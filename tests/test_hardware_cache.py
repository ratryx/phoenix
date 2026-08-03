import pytest
from modules.core.hardware_cache import _has_dynamic_metrics

def test_cache_aceita_percentual_uso_nos_volumes():
    data = {
        "armazenamento": {
            "volumes": [
                {
                    "nome": "C:",
                    "percentual_uso": 50.0
                }
            ]
        }
    }
    assert _has_dynamic_metrics(data) is False

def test_cache_rejeita_percentual_uso_na_raiz():
    data = {
        "percentual_uso": 50.0
    }
    assert _has_dynamic_metrics(data) is True

def test_cache_rejeita_percentual_uso_em_outro_lugar():
    data = {
        "cpu": {
            "percentual_uso": 50.0
        }
    }
    assert _has_dynamic_metrics(data) is True

def test_cache_rejeita_uso_percentual_mesmo_no_volume():
    data = {
        "armazenamento": {
            "volumes": [
                {
                    "nome": "C:",
                    "uso_percentual": 50.0
                }
            ]
        }
    }
    assert _has_dynamic_metrics(data) is True

def test_cache_rejeita_lista_com_uso_percentual_na_raiz():
    data = [
        {"uso_percentual": 50.0}
    ]
    assert _has_dynamic_metrics(data) is True
