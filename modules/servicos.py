"""
Módulo de gerenciamento de serviços do Windows.

Permite visualizar e desativar com segurança serviços que normalmente
não são necessários para o uso comum do PC, ajudando a liberar RAM e CPU.

IMPORTANTE: a lista SERVICOS_SEGUROS contém apenas serviços que, na grande
maioria dos casos, podem ser desativados sem causar problemas (telemetria,
recursos não usados, etc). Serviços essenciais do Windows NUNCA são
incluídos aqui de propósito, para não travar o PC do cliente.
"""

import subprocess
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich import box

from modules.shared import console


# Serviços que geralmente podem ser desativados com segurança em PCs domésticos/escritório.
# Formato: nome_interno_do_servico -> (nome amigável, descrição curta)
SERVICOS_SEGUROS = {
    "DiagTrack": ("Telemetria do Windows", "Coleta dados de uso para a Microsoft"),
    "dmwappushservice": ("Serviço de roteamento WAP", "Usado por notificações push corporativas"),
    "RetailDemo": ("Modo demonstração de loja", "Só usado em PCs de vitrine de loja"),
    "MapsBroker": ("Mapas offline do Windows", "Baixa mapas offline automaticamente"),
    "WSearch": ("Indexação de pesquisa do Windows", "Indexa arquivos para busca mais rápida (pode pesar em HDs)"),
    "SysMain": ("SuperFetch/SysMain", "Pré-carrega apps na RAM (recomendado desativar em SSD)"),
    "Fax": ("Serviço de Fax", "Quase ninguém usa fax atualmente"),
    "PrintNotify": ("Notificações de impressão", "Só necessário se usa impressora com frequência"),
    "RemoteRegistry": ("Registro remoto", "Permite acesso remoto ao registro (risco de segurança se não usado)"),
    "TabletInputService": ("Serviço de entrada para tablets", "Só necessário em notebooks 2-em-1/tablets"),
}


def listar_status_servicos() -> list:
    """Consulta o status atual (rodando/parado) de cada serviço da lista segura."""
    resultados = []
    for nome_servico, (nome_amigavel, descricao) in SERVICOS_SEGUROS.items():
        try:
            saida = subprocess.run(
                ["sc", "query", nome_servico],
                capture_output=True, text=True, timeout=10
            )
            if "RUNNING" in saida.stdout:
                status = "Rodando"
            elif "STOPPED" in saida.stdout:
                status = "Parado"
            elif saida.returncode != 0:
                status = "Não encontrado"
            else:
                status = "Desconhecido"
        except Exception:
            status = "Erro ao consultar"

        resultados.append({
            "nome_servico": nome_servico,
            "nome_amigavel": nome_amigavel,
            "descricao": descricao,
            "status": status,
        })
    return resultados


def exibir_servicos():
    """Exibe uma tabela com o status de todos os serviços gerenciáveis."""
    servicos = listar_status_servicos()

    tabela = Table(title="Serviços Gerenciáveis do Windows", box=box.ROUNDED, border_style="orange3")
    tabela.add_column("#", style="dim")
    tabela.add_column("Serviço", style="bold white")
    tabela.add_column("Descrição", style="dim white")
    tabela.add_column("Status", justify="center")

    for i, s in enumerate(servicos, start=1):
        cor_status = {
            "Rodando": "[green]Rodando[/green]",
            "Parado": "[yellow]Parado[/yellow]",
            "Não encontrado": "[dim]Não encontrado[/dim]",
        }.get(s["status"], f"[red]{s['status']}[/red]")

        tabela.add_row(str(i), s["nome_amigavel"], s["descricao"], cor_status)

    console.print(tabela)
    return servicos


def _validar_nome_servico(nome_servico: str) -> bool:
    """Verifica se o nome do serviço está na lista de serviços seguros."""
    return nome_servico in SERVICOS_SEGUROS


def desativar_servico(nome_servico: str) -> bool:
    """Para e desativa a inicialização automática de um serviço específico."""
    if not _validar_nome_servico(nome_servico):
        console.print(f"  [red]✗[/red] Serviço '{nome_servico}' não está na lista de serviços seguros.")
        return False
    try:
        subprocess.run(["sc", "stop", nome_servico], capture_output=True, timeout=15)
        subprocess.run(["sc", "config", nome_servico, "start=", "disabled"], capture_output=True, timeout=15)
        return True
    except Exception:
        return False


def ativar_servico(nome_servico: str) -> bool:
    """Reativa um serviço (volta para início automático e inicia o serviço)."""
    if not _validar_nome_servico(nome_servico):
        console.print(f"  [red]✗[/red] Serviço '{nome_servico}' não está na lista de serviços seguros.")
        return False
    try:
        subprocess.run(["sc", "config", nome_servico, "start=", "auto"], capture_output=True, timeout=15)
        subprocess.run(["sc", "start", nome_servico], capture_output=True, timeout=15)
        return True
    except Exception:
        return False


def menu_gerenciar_servicos():
    """Fluxo interativo para o usuário escolher quais serviços desativar."""
    console.print(Panel(
        "[bold yellow]Gerenciamento de Serviços[/bold yellow]\n"
        "[dim]Estes serviços normalmente podem ser desativados sem causar problemas. "
        "Avalie o uso do cliente antes de desativar (ex: não desative Fax se ele usa fax).[/dim]",
        border_style="orange3"
    ))

    servicos = exibir_servicos()

    console.print()
    if not Confirm.ask("[bold]Deseja desativar algum serviço da lista?[/bold]", default=False):
        return

    numeros = console.input(
        "\n[bold white]Digite os números dos serviços a desativar (separados por vírgula, ex: 1,3,5):[/bold white] "
    )

    try:
        indices = [int(n.strip()) - 1 for n in numeros.split(",") if n.strip().isdigit()]
    except ValueError:
        console.print("[red]Entrada inválida.[/red]")
        return

    for idx in indices:
        if 0 <= idx < len(servicos):
            servico = servicos[idx]
            if desativar_servico(servico["nome_servico"]):
                console.print(f"  [green]✓[/green] {servico['nome_amigavel']} desativado")
            else:
                console.print(f"  [red]✗[/red] Falha ao desativar {servico['nome_amigavel']}")

    console.print(Panel("[bold green]Serviços atualizados![/bold green]", border_style="green"))


if __name__ == "__main__":
    menu_gerenciar_servicos()
