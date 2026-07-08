"""
Phoenix Optimizer — Launcher

Ponto de entrada único do programa. Detecta o hardware da máquina,
recomenda automaticamente o modo de execução (CLI leve ou GUI completa)
e inicia o modo escolhido pelo usuário.

Ambos os modos chamam exatamente as mesmas funções em modules/ — não há
duplicação de lógica entre eles, apenas a forma de interação muda.

Como usar:
    python launcher.py
"""

import sys
import ctypes

def setup_console() -> bool:
    """
    Tenta anexar o processo ao console do processo pai quando necessário.
    Retorna True se o processo possui ou conseguiu anexar-se a um console.
    """
    if sys.platform != "win32":
        return sys.stdout.isatty()

    kernel32 = ctypes.windll.kernel32
    
    # Verifica se já possui um console associado
    if kernel32.GetConsoleWindow() != 0:
        return True

    # Se não possui, tenta anexar ao console do processo pai (ex: CMD/PowerShell)
    ATTACH_PARENT_PROCESS = -1
    if kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
        try:
            # Redireciona os fluxos padrão para o console anexado
            sys.stdout = open("CONOUT$", "w", encoding="utf-8")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8")
            sys.stdin = open("CONIN$", "r", encoding="utf-8")
            return True
        except Exception:
            return False
            
    return False

HAS_CONSOLE = setup_console()

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from modules import banner, hardware

console = Console()


def exibir_tela_escolha_modo(hw_info: dict, recomendacao: str):
    """Exibe a tela de escolha entre modo CLI e GUI, com recomendação baseada no hardware."""
    console.clear()
    banner.exibir_banner(modo="Seleção inicial")

    cpu = hw_info["cpu"]
    ram = hw_info["ram"]
    tem_gpu = len(hw_info["gpus"]) > 0

    resumo = (
        f"CPU: {cpu['nucleos_logicos']} núcleos lógicos   |   "
        f"RAM: {ram['total_gb']} GB   |   "
        f"GPU dedicada: {'Sim' if tem_gpu else 'Não detectada'}"
    )
    console.print(Panel(resumo, border_style=banner.COR_SECUNDARIA, title="Hardware detectado"))
    console.print()

    if recomendacao == "alto":
        texto_rec = (
            "[bold]Seu computador possui recursos suficientes para a interface gráfica.[/bold]\n"
            "Recomendamos o [bold]Modo GUI[/bold], mas o Modo CLI também está disponível."
        )
    elif recomendacao == "medio":
        texto_rec = (
            "Seu computador roda bem os dois modos.\n"
            "O [bold]Modo GUI[/bold] oferece mais visual; o [bold]Modo CLI[/bold] é mais leve e rápido."
        )
    else:
        texto_rec = (
            "[bold]Recomendamos o Modo CLI[/bold] para este computador, por consumir menos recursos.\n"
            "O Modo GUI funciona, mas pode ficar mais lento neste hardware."
        )

    console.print(Panel(texto_rec, border_style=banner.COR_PRIMARIA, title="Recomendação"))
    console.print()

    opcoes = """
[bold]1[/bold] - Modo CLI (terminal, leve, rápido)
[bold]2[/bold] - Modo GUI (interface gráfica completa)
[bold]0[/bold] - Sair
    """
    console.print(Panel(opcoes, border_style=banner.COR_SECUNDARIA, title="Como deseja continuar?"))

    return Prompt.ask("[bold white]Escolha uma opção[/bold white]", default="1" if recomendacao == "baixo" else "2")


def main():
    if not HAS_CONSOLE:
        try:
            hw_info = hardware.coletar_hardware_completo()
            from modules import gui_app
            gui_app.iniciar(hw_info)
            return
        except Exception as e:
            try:
                import traceback
                from modules import logs
                id_atend = logs.gerar_id_atendimento()
                logs.registrar_acao(id_atend, f"Erro critico GUI (sem console): {str(e)}\n{traceback.format_exc()}")
            except Exception:
                pass
            sys.exit(1)

    console.clear()
    banner.exibir_banner(modo="Iniciando...")
    console.print(Panel("Detectando hardware do sistema...", border_style=banner.COR_SECUNDARIA))

    hw_info = hardware.coletar_hardware_completo()
    recomendacao = hardware.classificar_capacidade_hardware(hw_info)

    escolha = exibir_tela_escolha_modo(hw_info, recomendacao)

    if escolha == "1":
        from modules import cli_app
        cli_app.iniciar(hw_info)
    elif escolha == "2":
        try:
            from modules import gui_app
            gui_app.iniciar(hw_info)
        except ImportError as e:
            console.print(Panel(
                f"[bold red]Não foi possível iniciar o Modo GUI.[/bold red]\n"
                f"Detalhe: {e}\n\n"
                "Verifique se o pacote 'pywebview' está instalado "
                "(pip install pywebview).\n"
                "Iniciando Modo CLI como alternativa...",
                border_style="red"
            ))
            from modules import cli_app
            cli_app.iniciar(hw_info)
    else:
        console.print(Panel("Encerrando o Phoenix Optimizer.", border_style=banner.COR_SECUNDARIA))
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Programa encerrado pelo usuário.[/yellow]")
        sys.exit(0)
    except Exception as e:
        import traceback
        console.print("\n[bold red]Ocorreu um erro inesperado:[/bold red]")
        console.print(f"[red]{e}[/red]\n")
        console.print(traceback.format_exc())
        console.print("\n[bold yellow]Pressione ENTER para fechar...[/bold yellow]")
        input()
        sys.exit(1)
