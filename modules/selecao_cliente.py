"""
Módulo de seleção de cliente para modo Portable.
Exibido toda vez que o Phoenix Optimizer é aberto em pen drive.
"""

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from modules.shared import console, listar_clientes_portable
from modules import banner


def exibir_selecao_cli() -> str | None:
    """
    Exibe a tela de seleção de cliente no modo CLI.
    Retorna o nome do cliente selecionado ou None se cancelado.
    """
    console.clear()
    banner.exibir_banner(modo="Portable")
    
    clientes = listar_clientes_portable()
    
    if clientes:
        console.print(Panel(
            "[bold]Selecione o cliente ou crie um novo atendimento[/bold]\n"
            "[dim]Cada cliente tem seu próprio histórico e relatórios.[/dim]",
            border_style=banner.COR_PRIMARIA
        ))
        
        tabela = Table(box=box.ROUNDED, border_style=banner.COR_PRIMARIA)
        tabela.add_column("#", style="dim", width=4)
        tabela.add_column("Cliente", style="bold white")
        tabela.add_column("Último atendimento", style="yellow")
        tabela.add_column("Atendimentos", justify="center")
        
        for i, c in enumerate(clientes, start=1):
            tabela.add_row(
                str(i),
                c['nome'],
                c['ultimo_atendimento'] or "Nunca",
                str(c['total_atendimentos'])
            )
        
        console.print(tabela)
        console.print()
        console.print(f"[dim]Digite o número para selecionar, ou 0 para novo cliente[/dim]")
        
        escolha = Prompt.ask(
            "Escolha", 
            default="0"
        )
        
        if escolha.isdigit():
            idx = int(escolha)
            if 1 <= idx <= len(clientes):
                cliente = clientes[idx - 1]
                console.print(f"\n[green]✓[/green] Cliente selecionado: [bold]{cliente['nome']}[/bold]")
                return cliente['nome']
    else:
        console.print(Panel(
            "[bold]Primeiro atendimento![/bold]\n"
            "[dim]Nenhum cliente cadastrado ainda. Vamos começar.[/dim]",
            border_style=banner.COR_PRIMARIA
        ))
    
    # Criar novo cliente
    console.print()
    nome = Prompt.ask(
        "[bold white]Nome do cliente ou PC[/bold white]",
        default=""
    ).strip()
    
    if not nome:
        if not Confirm.ask("Continuar sem identificar o cliente?", default=False):
            return None
        nome = "Cliente sem nome"
    
    console.print(f"\n[green]✓[/green] Novo cliente: [bold]{nome}[/bold]")
    return nome


def exibir_selecao_gui() -> str | None:
    """
    Retorna o nome do cliente selecionado via GUI.
    A interface real é exibida pelo frontend JS.
    """
    pass
