"""
Módulo de relatório: compara o snapshot do PC "antes" da otimização
com o snapshot "depois", mostrando ganhos de forma visual.
Ótima ferramenta de venda — mostra pro cliente o que foi feito de verdade.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def _seta_variacao(valor_antes: float, valor_depois: float, menor_e_melhor: bool = True) -> str:
    """
    Retorna uma seta colorida indicando se o valor melhorou ou piorou.
    menor_e_melhor=True: significa que diminuir o valor é bom (ex: uso de RAM).
    menor_e_melhor=False: significa que aumentar o valor é bom (ex: RAM disponível).
    """
    diferenca = valor_depois - valor_antes

    if abs(diferenca) < 0.01:
        return "[dim]= sem alteração[/dim]"

    melhorou = (diferenca < 0) if menor_e_melhor else (diferenca > 0)

    if melhorou:
        return f"[bold green]▼ {abs(diferenca):.2f}[/bold green]" if menor_e_melhor else f"[bold green]▲ {abs(diferenca):.2f}[/bold green]"
    else:
        return f"[bold red]▲ {abs(diferenca):.2f}[/bold red]" if menor_e_melhor else f"[bold red]▼ {abs(diferenca):.2f}[/bold red]"


def gerar_relatorio_comparativo(snapshot_antes: dict, snapshot_depois: dict, espaco_liberado_mb: float = 0):
    """
    Gera e exibe no terminal um relatório comparativo entre dois snapshots
    de diagnóstico (antes e depois da limpeza/otimização).
    """
    dados_antes = snapshot_antes["dados"]
    dados_depois = snapshot_depois["dados"]

    cliente = snapshot_antes.get("cliente", "não informado")

    console.print(Panel(
        f"[bold yellow]Relatório de Otimização — Cliente: {cliente}[/bold yellow]",
        border_style="orange3"
    ))

    # Tabela CPU e Memória
    tabela = Table(title="CPU & Memória — Antes vs Depois", box=box.ROUNDED, border_style="orange3")
    tabela.add_column("Métrica", style="bold white")
    tabela.add_column("Antes", style="yellow")
    tabela.add_column("Depois", style="yellow")
    tabela.add_column("Variação", justify="center")

    cpu_antes = dados_antes["cpu"]["uso_percentual"]
    cpu_depois = dados_depois["cpu"]["uso_percentual"]
    tabela.add_row(
        "Uso de CPU (%)", f"{cpu_antes}%", f"{cpu_depois}%",
        _seta_variacao(cpu_antes, cpu_depois, menor_e_melhor=True)
    )

    ram_antes = dados_antes["memoria"]["percentual_uso"]
    ram_depois = dados_depois["memoria"]["percentual_uso"]
    tabela.add_row(
        "Uso de RAM (%)", f"{ram_antes}%", f"{ram_depois}%",
        _seta_variacao(ram_antes, ram_depois, menor_e_melhor=True)
    )

    ram_disp_antes = dados_antes["memoria"]["disponivel_gb"]
    ram_disp_depois = dados_depois["memoria"]["disponivel_gb"]
    tabela.add_row(
        "RAM disponível (GB)", f"{ram_disp_antes} GB", f"{ram_disp_depois} GB",
        _seta_variacao(ram_disp_antes, ram_disp_depois, menor_e_melhor=False)
    )

    console.print(tabela)

    # Tabela de disco (espaço livre)
    discos_antes = {d["unidade"]: d for d in dados_antes["discos"]}
    discos_depois = {d["unidade"]: d for d in dados_depois["discos"]}

    tabela_disco = Table(title="Armazenamento — Antes vs Depois", box=box.ROUNDED, border_style="orange3")
    tabela_disco.add_column("Unidade", style="bold white")
    tabela_disco.add_column("Livre Antes", style="yellow")
    tabela_disco.add_column("Livre Depois", style="yellow")
    tabela_disco.add_column("Variação", justify="center")

    for unidade, info_antes in discos_antes.items():
        info_depois = discos_depois.get(unidade)
        if not info_depois:
            continue
        tabela_disco.add_row(
            unidade,
            f"{info_antes['livre_gb']} GB",
            f"{info_depois['livre_gb']} GB",
            _seta_variacao(info_antes["livre_gb"], info_depois["livre_gb"], menor_e_melhor=False)
        )

    console.print(tabela_disco)

    # Resumo final
    resumo = f"[bold white]Espaço total liberado: [bold green]{espaco_liberado_mb:.2f} MB[/bold green][/bold white]\n"

    ganho_ram = ram_disp_depois - ram_disp_antes
    if ganho_ram > 0:
        resumo += f"[bold white]RAM adicional disponível: [bold green]{ganho_ram:.2f} GB[/bold green][/bold white]\n"

    reducao_cpu = cpu_antes - cpu_depois
    if reducao_cpu > 0:
        resumo += f"[bold white]Redução no uso de CPU: [bold green]{reducao_cpu:.1f}%[/bold green][/bold white]"

    console.print(Panel(resumo, title="[bold yellow]Resumo do Atendimento[/bold yellow]", border_style="green"))


def exportar_relatorio_txt(snapshot_antes: dict, snapshot_depois: dict, espaco_liberado_mb: float, caminho_saida) -> None:
    """Exporta o relatório comparativo em formato .txt simples, pra entregar/mostrar ao cliente."""
    dados_antes = snapshot_antes["dados"]
    dados_depois = snapshot_depois["dados"]
    cliente = snapshot_antes.get("cliente", "não informado")

    linhas = [
        "=" * 50,
        "PHOENIX OPTIMIZER - RELATÓRIO DE ATENDIMENTO",
        "=" * 50,
        f"Cliente: {cliente}",
        f"Data: {snapshot_depois.get('data_hora', '')}",
        "",
        "--- CPU & MEMÓRIA ---",
        f"Uso de CPU:      {dados_antes['cpu']['uso_percentual']}%  ->  {dados_depois['cpu']['uso_percentual']}%",
        f"Uso de RAM:      {dados_antes['memoria']['percentual_uso']}%  ->  {dados_depois['memoria']['percentual_uso']}%",
        f"RAM disponível:  {dados_antes['memoria']['disponivel_gb']} GB  ->  {dados_depois['memoria']['disponivel_gb']} GB",
        "",
        "--- ARMAZENAMENTO ---",
    ]

    discos_antes = {d["unidade"]: d for d in dados_antes["discos"]}
    discos_depois = {d["unidade"]: d for d in dados_depois["discos"]}
    for unidade, info_antes in discos_antes.items():
        info_depois = discos_depois.get(unidade)
        if info_depois:
            linhas.append(
                f"{unidade}  Livre: {info_antes['livre_gb']} GB  ->  {info_depois['livre_gb']} GB"
            )

    linhas.append("")
    linhas.append(f"Espaço total liberado: {espaco_liberado_mb:.2f} MB")
    linhas.append("=" * 50)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
