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
from rich.progress import Progress, SpinnerColumn, TextColumn

from modules import banner, hardware

console = Console()


def exibir_tela_escolha_modo():
    """Exibe a tela de escolha entre modo CLI e GUI."""
    console.clear()
    banner.exibir_banner(modo="Seleção inicial")

    texto_rec = (
        "O [bold]Modo GUI[/bold] oferece uma interface gráfica completa.\n"
        "O [bold]Modo CLI[/bold] é executado diretamente no terminal (mais leve e rápido)."
    )

    console.print(Panel(texto_rec, border_style=banner.COR_PRIMARIA, title="Modo de Execução"))
    console.print()

    opcoes = """
[bold]1[/bold] - Modo CLI (terminal, leve, rápido)
[bold]2[/bold] - Modo GUI (interface gráfica completa)
[bold]0[/bold] - Sair
    """
    console.print(Panel(opcoes, border_style=banner.COR_SECUNDARIA, title="Como deseja continuar?"))

    return Prompt.ask("[bold white]Escolha uma opção[/bold white]", default="2")


def _iniciar_modo_portable() -> bool:
    """
    Controla o fluxo inicial do modo Portable (seleção de cliente via CLI).
    Retorna True se o cliente foi selecionado com sucesso, False se o usuário cancelou.
    Se houver erro crítico na seleção, o programa é encerrado (sys.exit(1)).
    """
    from modules import selecao_cliente
    from modules.shared import selecionar_cliente_portable

    cliente_escolhido = selecao_cliente.exibir_selecao_cli()
    if not cliente_escolhido:
        return False

    res = selecionar_cliente_portable(cliente_escolhido["id"])
    if not res.get("ok"):
        console.print(f"\n[bold red]Erro ao selecionar o cliente: {res.get('erro')}[/bold red]")
        console.print("[dim]O programa será encerrado.[/dim]")
        sys.exit(1)

    return True

def main():
    console.clear()
    banner.exibir_banner(modo="Iniciando...")

    escolha = exibir_tela_escolha_modo()

    if escolha == "0":
        console.print(Panel("Encerrando o Phoenix Optimizer.", border_style=banner.COR_SECUNDARIA))
        sys.exit(0)

    from modules.shared import IS_PORTABLE

    if IS_PORTABLE:
        if not _iniciar_modo_portable():
            sys.exit(0)

    if escolha == "1":
        # Modo CLI
        hw_info = None
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Detectando hardware do sistema...", total=None)

            def update_progress(msg):
                progress.update(task, description=f"[cyan]{msg}")

            hw_info = hardware.obter_hardware_com_cache(progress_callback=update_progress)
            progress.update(task, description="[green]Hardware detectado com sucesso!")
        
        from modules import cli_app
        cli_app.iniciar(hw_info)
    elif escolha == "2":
        # Modo GUI
        console.print("\n[cyan]Modo GUI em execução.[/cyan]")
        console.print("[yellow]Feche a interface gráfica ou esta janela para encerrar o Phoenix Optimizer.[/yellow]\n")
        try:
            from modules import gui_app
            gui_app.iniciar(None)
        except ImportError as e:
            console.print(Panel(
                f"[bold red]Não foi possível iniciar o Modo GUI.[/bold red]\n"
                f"Detalhe: {e}\n\n"
                "Verifique se o pacote 'pywebview' está instalado "
                "(pip install pywebview).\n"
                "Iniciando Modo CLI como alternativa...",
                border_style="red"
            ))
            
            # Se falhou e vai pro CLI, precisamos coletar hardware
            hw_info = hardware.obter_hardware_com_cache()
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
