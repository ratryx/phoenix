from modules.gui_app import PhoenixAPI
import pytest

def test_instanciar_api_sem_janela():
    # Deve ser possível instanciar sem crash
    api = PhoenixAPI({"cpu": "mocked", "ram": "mocked", "gpus": []})
    assert api._janela is None
    assert api.obter_hardware() == {"cpu": "mocked", "ram": "mocked", "gpus": []}

def test_metodo_leve_mockado(monkeypatch):
    # Usaremos monkeypatch num módulo para garantir que métodos leves retornam
    from modules import hardware
    monkeypatch.setattr(hardware, "classificar_capacidade_hardware", lambda x: "alto")
    
    api = PhoenixAPI({})
    assert api.obter_nivel_qualidade_visual() == "alto"

def test_metodos_assincronos_retornam_job_id(monkeypatch):
    # Impedimos a limpeza de fato de rodar e destruir algo
    from modules import limpeza
    monkeypatch.setattr(limpeza, "executar_limpeza_completa", lambda x: 100)
    
    api = PhoenixAPI({})
    res = api.executar_limpeza()
    assert "job_id" in res
    assert len(res["job_id"]) > 10

def test_janela_nao_serializada():
    api = PhoenixAPI({})
    # No pywebview, atributos ou metodos iniciados com _ não são expostos
    # Para validar, verificamos se _janela inicia com underline e se 
    # não há métodos/atributos de interface que quebrem
    import inspect
    public_attrs = [a for a in dir(api) if not a.startswith('_') and not callable(getattr(api, a))]
    assert "janela" not in public_attrs
    assert hasattr(api, "_janela")
