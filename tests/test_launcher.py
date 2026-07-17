import launcher
import pytest
from unittest.mock import MagicMock

def test_exibir_tela_escolha_modo(monkeypatch):
    # Mocking o Prompt.ask do rich
    from rich.prompt import Prompt
    monkeypatch.setattr(Prompt, "ask", lambda *args, **kwargs: "1")
    
    # Mocking as chamadas do console.print para nao poluir o stdout real
    monkeypatch.setattr(launcher.console, "print", lambda *args, **kwargs: None)
    monkeypatch.setattr(launcher.console, "clear", lambda *args, **kwargs: None)
    
    # Prevenimos a renderizacao do banner
    from modules import banner
    monkeypatch.setattr(banner, "exibir_banner", lambda *args, **kwargs: None)
    
    hw_info = {
        "cpu": {"nucleos_logicos": 4},
        "ram": {"total_gb": 8},
        "gpus": []
    }
    
    escolha = launcher.exibir_tela_escolha_modo(hw_info, "baixo")
    assert escolha == "1"

def test_decisao_main_chamada_cli(monkeypatch):
    # Testar se a escolha 1 realmente chama o CLI sem abrir a GUI
    from modules import cli_app, gui_app
    
    cli_iniciado = False
    def mock_cli_iniciar(hw_info):
        nonlocal cli_iniciado
        cli_iniciado = True
        
    monkeypatch.setattr(cli_app, "iniciar", mock_cli_iniciar)
    monkeypatch.setattr(gui_app, "iniciar", lambda hw: pytest.fail("A GUI não deveria ser chamada aqui"))
    
    monkeypatch.setattr(launcher, "exibir_tela_escolha_modo", lambda *args, **kwargs: "1")
    monkeypatch.setattr(launcher, "HAS_CONSOLE", True)
    
    # Mock IS_PORTABLE
    import modules.shared
    monkeypatch.setattr(modules.shared, "IS_PORTABLE", False)
    
    # Previne a detecção demorada de hardware
    from modules import hardware
    monkeypatch.setattr(hardware, "obter_hardware_com_cache", lambda **kwargs: {})
    monkeypatch.setattr(hardware, "classificar_capacidade_hardware", lambda x: "baixo")
    
    # Previne progress do rich
    from rich.progress import Progress
    monkeypatch.setattr(Progress, "__enter__", MagicMock())
    monkeypatch.setattr(Progress, "__exit__", MagicMock())
    
    monkeypatch.setattr(launcher.console, "clear", lambda *args, **kwargs: None)
    from modules import banner
    monkeypatch.setattr(banner, "exibir_banner", lambda *args, **kwargs: None)
    
    launcher.main()
    
    assert cli_iniciado is True
