"""
Phoenix Optimizer — Modo CLI

Implementa o menu interativo via terminal, usando o núcleo compartilhado
em modules/. Esta é a versão leve, recomendada para computadores com
menos recursos.

Chamado pelo launcher.py — não execute este arquivo diretamente em produção.
"""

import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from modules import banner
from modules import diagnostico
from modules import limpeza
from modules import otimizacao
from modules import servicos
from modules import logs
from modules import relatorio
from modules import hardware as hardware_mod

console = Console()

ESTADO = {
    "id_atendimento": None,
    "nome_cliente": "",
}


def exibir_menu():
    """Exibe o menu principal de opções."""
    opcoes = f"""
[bold]1[/bold]  - Diagnóstico completo do PC
[bold]2[/bold]  - Hardware detalhado (CPU, RAM, GPU)
[bold]3[/bold]  - Limpeza de arquivos temporários e lixo
[bold]4[/bold]  - Otimização geral de performance
[bold]5[/bold]  - Otimização para jogos (ganho de FPS)
[bold]6[/bold]  - Gerenciar serviços do Windows
[bold]7[/bold]  - Listar programas de inicialização
[bold]8[/bold]  - Otimizar disco (TRIM/desfragmentação)
[bold]9[/bold]  - Ver histórico de atendimentos
[bold]10[/bold] - [bold {banner.COR_PRIMARIA}]Executar ROTINA COMPLETA[/bold {banner.COR_PRIMARIA}] (recomendado p/ atendimento)
[bold]0[/bold]  - Sair
    """
    console.print(Panel(opcoes, title="Menu Principal", border_style=banner.COR_PRIMARIA, box=box.ROUNDED))


def pausar():
    Prompt.ask(f"\n[{banner.COR_SECUNDARIA}]Pressione ENTER para voltar ao menu[/{banner.COR_SECUNDARIA}]", default="")


def iniciar_atendimento():
    """Pede o nome do cliente (opcional) e cria um novo ID de atendimento."""
    console.print(Panel(
        "Novo atendimento\n[dim]Deixe em branco caso não queira identificar o cliente.[/dim]",
        border_style=banner.COR_PRIMARIA
    ))
    nome = Prompt.ask("Nome do cliente", default="")
    ESTADO["nome_cliente"] = nome
    ESTADO["id_atendimento"] = logs.gerar_id_atendimento()
    return ESTADO["id_atendimento"]


def fluxo_hardware_detalhado(hw_info: dict):
    """Exibe informações detalhadas de hardware, incluindo GPU."""
    cpu = hw_info["cpu"]
    ram = hw_info["ram"]
    gpus = hw_info["gpus"]

    tabela_cpu = Table(title="Processador", box=box.ROUNDED, border_style=banner.COR_PRIMARIA)
    tabela_cpu.add_column("Item", style="bold white")
    tabela_cpu.add_column("Valor")
    tabela_cpu.add_row("Modelo", cpu["modelo"])
    tabela_cpu.add_row("Núcleos físicos / lógicos", f"{cpu['nucleos_fisicos']} / {cpu['nucleos_logicos']}")
    if cpu.get("frequencia_atual_mhz"):
        tabela_cpu.add_row("Frequência atual", f"{cpu['frequencia_atual_mhz']:.0f} MHz")
    tabela_cpu.add_row("Uso atual", f"{cpu['uso_percentual']}%")
    console.print(tabela_cpu)

    tabela_ram = Table(title="Memória RAM", box=box.ROUNDED, border_style=banner.COR_PRIMARIA)
    tabela_ram.add_column("Item", style="bold white")
    tabela_ram.add_column("Valor")
    tabela_ram.add_row("Total", f"{ram['total_gb']} GB")
    tabela_ram.add_row("Disponível", f"{ram['disponivel_gb']} GB")
    tabela_ram.add_row("Uso atual", f"{ram['percentual_uso']}%")
    console.print(tabela_ram)

    if not gpus:
        console.print(Panel("Nenhuma GPU detectada.", border_style=banner.COR_SECUNDARIA))
    else:
        for gpu in gpus:
            tabela_gpu = Table(title=f"GPU — {gpu['nome']}", box=box.ROUNDED, border_style=banner.COR_PRIMARIA)
            tabela_gpu.add_column("Item", style="bold white")
            tabela_gpu.add_column("Valor")
            tabela_gpu.add_row("Fabricante", gpu.get("fabricante", "Desconhecido"))
            if gpu.get("vram_total_mb"):
                vram_gb = gpu["vram_total_mb"] / 1024
                tabela_gpu.add_row("VRAM total", f"{vram_gb:.1f} GB")
            if gpu.get("vram_usada_mb") is not None:
                vram_usada_gb = gpu["vram_usada_mb"] / 1024
                tabela_gpu.add_row("VRAM em uso", f"{vram_usada_gb:.1f} GB")
            if gpu.get("uso_percentual") is not None:
                tabela_gpu.add_row("Uso atual", f"{gpu['uso_percentual']}%")
            if gpu.get("temperatura_c") is not None:
                tabela_gpu.add_row("Temperatura", f"{gpu['temperatura_c']}°C")
            if gpu.get("driver_versao"):
                tabela_gpu.add_row("Versão do driver", gpu["driver_versao"])
            tabela_gpu.add_row("Origem dos dados", gpu.get("fonte_dados", "—"))
            console.print(tabela_gpu)


def _executar_fluxo_restauracao_cli() -> bool:
    """
    Executa o fluxo de ponto de restauração na CLI.
    Retorna True se puder prosseguir com as otimizações, False caso contrário.
    """
    console.print("\n[bold]Verificando e criando ponto de restauração do sistema...[/bold]")
    with console.status("[bold yellow]Invocando PowerShell Checkpoint-Computer (isso pode levar de 10 a 60 segundos)...") as status:
        res = otimizacao.criar_ponto_restauracao()

    if res.get("ok"):
        console.print(f"  [green]✓[/green] {res['mensagem']}")
        if Confirm.ask("\nDeseja prosseguir com a aplicação das otimizações?", default=True):
            return True
        else:
            console.print("[yellow]Operação cancelada pelo usuário. Nenhuma otimização foi aplicada.[/yellow]")
            return False
    else:
        console.print(f"  [red]✗[/red] Falha ao criar ponto de restauração.")
        console.print(f"    [yellow]Motivo:[/yellow] {res['erro']}")

        if res.get("codigo") == "NO_ADMIN":
            console.print("[red]ERRO CRÍTICO: Não é possível prosseguir sem privilégios de Administrador.[/red]")
            return False

        if Confirm.ask("\nDeseja prosseguir com as otimizações mesmo assim (sem proteção)?", default=False):
            return True
        else:
            console.print("[yellow]Operação cancelada pelo usuário. Nenhuma otimização foi aplicada.[/yellow]")
            return False


def rotina_completa():
    """
    Executa a rotina padrão de atendimento:
    snapshot 'antes' -> limpeza -> otimização -> snapshot 'depois' -> relatório comparativo.
    """
    id_atendimento = iniciar_atendimento()

    console.print()
    banner.exibir_secao("Iniciando rotina completa Phoenix")
    time.sleep(0.3)

    console.print("\n[bold]Etapa 1/4 — Coletando diagnóstico inicial...[/bold]")
    dados_antes = diagnostico.coletar_diagnostico_silencioso()
    logs.salvar_snapshot(id_atendimento, "antes", dados_antes, ESTADO["nome_cliente"])
    logs.registrar_acao(id_atendimento, "Diagnóstico inicial coletado", nome_cliente=ESTADO["nome_cliente"])
    banner.msg_sucesso("Diagnóstico inicial salvo")

    console.print("\n[bold]Etapa 2/4 — Limpeza do sistema...[/bold]")
    espaco_liberado = limpeza.executar_limpeza_completa(id_atendimento)

    console.print("\n[bold]Etapa 3/4 — Otimização de performance...[/bold]")
    if _executar_fluxo_restauracao_cli():
        otimizacao.executar_otimizacao_geral(id_atendimento)
    else:
        console.print("[yellow]Etapa de otimização pulada pelo usuário.[/yellow]")

    console.print("\n[bold]Etapa 4/4 — Coletando diagnóstico final...[/bold]")
    dados_depois = diagnostico.coletar_diagnostico_silencioso()
    logs.salvar_snapshot(id_atendimento, "depois", dados_depois, ESTADO["nome_cliente"])
    logs.registrar_acao(id_atendimento, "Diagnóstico final coletado")
    banner.msg_sucesso("Diagnóstico final salvo")

    console.print()
    snapshot_antes = logs.carregar_snapshot(id_atendimento, "antes")
    snapshot_depois = logs.carregar_snapshot(id_atendimento, "depois")
    espaco_liberado_mb = espaco_liberado / (1024 ** 2)

    relatorio.gerar_relatorio_comparativo(snapshot_antes, snapshot_depois, espaco_liberado_mb)

    pasta_logs = logs.obter_pasta_logs()
    caminho_txt = pasta_logs / f"{id_atendimento}_relatorio.txt"
    relatorio.exportar_relatorio_txt(snapshot_antes, snapshot_depois, espaco_liberado_mb, caminho_txt)
    console.print(f"\n[{banner.COR_SECUNDARIA}]Relatório exportado em: {caminho_txt}[/{banner.COR_SECUNDARIA}]")

    console.print(Panel(
        "Rotina completa finalizada! PC limpo e otimizado.",
        border_style=banner.COR_SUCESSO
    ))


def fluxo_limpeza_avulsa():
    id_atendimento = None
    if Confirm.ask("Deseja registrar esta limpeza em um atendimento?", default=False):
        id_atendimento = iniciar_atendimento()
    limpeza.executar_limpeza_completa(id_atendimento)


def fluxo_otimizacao_geral_avulsa():
    id_atendimento = None
    if Confirm.ask("Deseja registrar esta otimização em um atendimento?", default=False):
        id_atendimento = iniciar_atendimento()
    if _executar_fluxo_restauracao_cli():
        otimizacao.executar_otimizacao_geral(id_atendimento)


def fluxo_otimizacao_gaming_avulsa():
    id_atendimento = None
    if Confirm.ask("Deseja registrar esta otimização em um atendimento?", default=False):
        id_atendimento = iniciar_atendimento()
    if _executar_fluxo_restauracao_cli():
        otimizacao.executar_otimizacao_gaming(id_atendimento)


def iniciar(hw_info: dict = None):
    """Ponto de entrada do modo CLI, chamado pelo launcher.py."""
    if hw_info is None:
        hw_info = hardware_mod.coletar_hardware_completo()

    console.clear()
    banner.exibir_banner(modo="CLI")

    while True:
        exibir_menu()
        escolha = Prompt.ask("Escolha uma opção", default="0")

        console.print()

        try:
            if escolha == "1":
                diagnostico.executar_diagnostico_completo()
                pausar()
            elif escolha == "2":
                fluxo_hardware_detalhado(hw_info)
                pausar()
            elif escolha == "3":
                fluxo_limpeza_avulsa()
                pausar()
            elif escolha == "4":
                fluxo_otimizacao_geral_avulsa()
                pausar()
            elif escolha == "5":
                fluxo_otimizacao_gaming_avulsa()
                pausar()
            elif escolha == "6":
                if _executar_fluxo_restauracao_cli():
                    servicos.menu_gerenciar_servicos()
                else:
                    console.print("[yellow]Gerenciamento de serviços cancelado.[/yellow]")
                pausar()
            elif escolha == "7":
                resultado = otimizacao.listar_itens_inicializacao()
                console.print(Panel(resultado, title="Itens de inicialização", border_style=banner.COR_PRIMARIA))
                pausar()
            elif escolha == "8":
                banner.exibir_secao("Otimizando disco — isso pode levar alguns minutos")
                otimizacao.otimizar_disco_principal()
                pausar()
            elif escolha == "9":
                logs.exibir_historico()
                pausar()
            elif escolha == "10":
                rotina_completa()
                pausar()
            elif escolha == "0":
                console.print(Panel("Obrigado por usar o Phoenix Optimizer!", border_style=banner.COR_PRIMARIA))
                break
            else:
                console.print("[red]Opção inválida, tente novamente.[/red]")
                time.sleep(1)
        except Exception as e:
            import traceback
            banner.msg_erro(f"Erro ao executar esta opção: {e}")
            console.print(f"[{banner.COR_SECUNDARIA}]" + traceback.format_exc() + f"[/{banner.COR_SECUNDARIA}]")
            pausar()

        console.clear()
        banner.exibir_banner(modo="CLI")


if __name__ == "__main__":
    try:
        iniciar()
    except KeyboardInterrupt:
        console.print("\n[yellow]Programa encerrado pelo usuário.[/yellow]")
        sys.exit(0)
