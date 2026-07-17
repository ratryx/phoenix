"""
Módulo de relatório: compara o snapshot do PC "antes" da otimização
com o snapshot "depois", mostrando ganhos de forma visual.
Ótima ferramenta de venda — mostra pro cliente o que foi feito de verdade.
"""

from rich.table import Table
from rich.panel import Panel
from rich import box

from modules.shared import console


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


def exportar_relatorio_html(snapshot_antes: dict, snapshot_depois: dict, espaco_liberado_mb: float, caminho_saida) -> None:
    """
    Exporta o relatório comparativo em formato HTML estilizado, pronto
    para abrir no navegador e imprimir como PDF (Ctrl+P → Salvar como PDF).
    Visual premium com a identidade visual do Phoenix Optimizer.
    """
    dados_antes = snapshot_antes["dados"]
    dados_depois = snapshot_depois["dados"]
    cliente = snapshot_antes.get("cliente", "não informado")
    data = snapshot_depois.get("data_hora", "")

    def _seta_html(antes: float, depois: float, menor_melhor: bool = True) -> str:
        diff = depois - antes
        if abs(diff) < 0.01:
            return '<span style="color:#888">= sem alteração</span>'
        melhorou = (diff < 0) if menor_melhor else (diff > 0)
        cor = "#4CAF50" if melhorou else "#F44336"
        seta = "▼" if diff < 0 else "▲"
        return f'<span style="color:{cor};font-weight:bold">{seta} {abs(diff):.2f}</span>'

    # Disco rows
    discos_antes = {d["unidade"]: d for d in dados_antes["discos"]}
    discos_depois = {d["unidade"]: d for d in dados_depois["discos"]}
    disco_rows = ""
    for unidade, info_antes in discos_antes.items():
        info_depois = discos_depois.get(unidade)
        if info_depois:
            variacao = _seta_html(info_antes["livre_gb"], info_depois["livre_gb"], menor_melhor=False)
            disco_rows += f"""
            <tr>
                <td>{unidade}</td>
                <td>{info_antes['livre_gb']} GB</td>
                <td>{info_depois['livre_gb']} GB</td>
                <td>{variacao}</td>
            </tr>"""

    cpu_antes = dados_antes["cpu"]["uso_percentual"]
    cpu_depois = dados_depois["cpu"]["uso_percentual"]
    ram_antes = dados_antes["memoria"]["percentual_uso"]
    ram_depois = dados_depois["memoria"]["percentual_uso"]
    ram_disp_antes = dados_antes["memoria"]["disponivel_gb"]
    ram_disp_depois = dados_depois["memoria"]["disponivel_gb"]

    ganho_ram = ram_disp_depois - ram_disp_antes
    reducao_cpu = cpu_antes - cpu_depois

    resumo_items = f'<li>Espaço liberado: <strong>{espaco_liberado_mb:.2f} MB</strong></li>'
    if ganho_ram > 0:
        resumo_items += f'<li>RAM adicional disponível: <strong>{ganho_ram:.2f} GB</strong></li>'
    if reducao_cpu > 0:
        resumo_items += f'<li>Redução no uso de CPU: <strong>{reducao_cpu:.1f}%</strong></li>'

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phoenix Optimizer - Relatório de Atendimento</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            padding: 40px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: #16213e;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            border: 1px solid rgba(216, 155, 74, 0.2);
        }}

        .header {{
            text-align: center;
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 2px solid rgba(216, 155, 74, 0.3);
        }}

        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            color: #D89B4A;
            letter-spacing: 2px;
            margin-bottom: 4px;
        }}

        .header .subtitle {{
            font-size: 14px;
            color: #8C8C8C;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .info-bar {{
            display: flex;
            justify-content: space-between;
            background: rgba(216, 155, 74, 0.08);
            border-radius: 8px;
            padding: 12px 20px;
            margin-bottom: 28px;
            font-size: 14px;
        }}

        .info-bar span {{ color: #ccc; }}
        .info-bar strong {{ color: #E8B96A; }}

        h2 {{
            font-size: 16px;
            font-weight: 600;
            color: #D89B4A;
            margin: 24px 0 12px 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}

        th {{
            background: rgba(216, 155, 74, 0.15);
            color: #E8B96A;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid rgba(216, 155, 74, 0.2);
        }}

        td {{
            padding: 10px 14px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 14px;
        }}

        tr:hover td {{
            background: rgba(255,255,255,0.02);
        }}

        .resumo {{
            background: linear-gradient(135deg, rgba(111, 174, 124, 0.1), rgba(216, 155, 74, 0.1));
            border: 1px solid rgba(111, 174, 124, 0.3);
            border-radius: 12px;
            padding: 20px 24px;
            margin-top: 28px;
        }}

        .resumo h2 {{
            color: #6FAE7C;
            margin-top: 0;
        }}

        .resumo ul {{
            list-style: none;
            padding: 0;
        }}

        .resumo li {{
            padding: 4px 0;
            font-size: 15px;
        }}

        .resumo li::before {{
            content: "✓ ";
            color: #6FAE7C;
            font-weight: bold;
        }}

        .footer {{
            text-align: center;
            margin-top: 32px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.05);
            font-size: 12px;
            color: #666;
        }}

        @media print {{
            body {{ background: white; color: #333; padding: 20px; }}
            .container {{ box-shadow: none; border: 1px solid #ddd; background: white; }}
            .header h1 {{ color: #B8860B; }}
            h2 {{ color: #B8860B; }}
            th {{ background: #f5f0e0; color: #B8860B; }}
            td {{ border-bottom-color: #eee; }}
            .info-bar {{ background: #f9f6f0; }}
            .resumo {{ background: #f0f8f0; border-color: #c8e6c9; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 PHOENIX OPTIMIZER</h1>
            <div class="subtitle">Relatório de Atendimento</div>
        </div>

        <div class="info-bar">
            <span>Cliente: <strong>{cliente}</strong></span>
            <span>Data: <strong>{data}</strong></span>
        </div>

        <h2>CPU &amp; Memória — Antes vs Depois</h2>
        <table>
            <thead>
                <tr><th>Métrica</th><th>Antes</th><th>Depois</th><th>Variação</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td>Uso de CPU</td>
                    <td>{cpu_antes}%</td>
                    <td>{cpu_depois}%</td>
                    <td>{_seta_html(cpu_antes, cpu_depois, menor_melhor=True)}</td>
                </tr>
                <tr>
                    <td>Uso de RAM</td>
                    <td>{ram_antes}%</td>
                    <td>{ram_depois}%</td>
                    <td>{_seta_html(ram_antes, ram_depois, menor_melhor=True)}</td>
                </tr>
                <tr>
                    <td>RAM disponível</td>
                    <td>{ram_disp_antes} GB</td>
                    <td>{ram_disp_depois} GB</td>
                    <td>{_seta_html(ram_disp_antes, ram_disp_depois, menor_melhor=False)}</td>
                </tr>
            </tbody>
        </table>

        <h2>Armazenamento — Antes vs Depois</h2>
        <table>
            <thead>
                <tr><th>Unidade</th><th>Livre Antes</th><th>Livre Depois</th><th>Variação</th></tr>
            </thead>
            <tbody>
                {disco_rows}
            </tbody>
        </table>

        <div class="resumo">
            <h2>Resumo do Atendimento</h2>
            <ul>
                {resumo_items}
            </ul>
        </div>

        <div class="footer">
            Phoenix Optimizer v2.0 — Diagnóstico e Otimização de Performance para Windows
        </div>
    </div>
</body>
</html>"""

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)
