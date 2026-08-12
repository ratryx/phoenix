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
    dados_antes = snapshot_antes
    dados_depois = snapshot_depois

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


def _formatar_status_limpeza(status: str, ignorados: int) -> str:
    status = status.lower()
    if status == "vazio":
        return "NADA A LIMPAR"
    if status == "parcial" or ignorados > 0:
        return "CONCLUÍDO COM EXCEÇÕES"
    elif status in ("concluido", "concluído"):
        return "CONCLUÍDO"
    elif status in ("erro", "falhou"):
        return "FALHOU"
    elif status in ("unsupported", "não aplicável", "nao aplicavel"):
        return "NÃO APLICÁVEL"
    return status.upper()

def exportar_relatorio_txt(payload: dict, snapshot_antes: dict, snapshot_depois: dict, caminho_saida) -> None:
    """Exporta o relatório técnico V3 em txt."""
    dados_antes = snapshot_antes
    dados_depois = snapshot_depois
    cliente = payload.get("cliente", "não informado")
    
    resumo = payload.get("resumo", {})
    limpeza = payload.get("limpeza", {})
    otim = payload.get("otimizacoes", {})
    prot = payload.get("protecao", {})
    analises = payload.get("analises", {})
    recs = payload.get("recomendacoes", [])
    
    protecao_status = prot.get("status", "N/D")
    if protecao_status == "restore_created":
        protecao_text = "Ponto de restauração criado e verificado"
    elif protecao_status == "risk_accepted":
        protecao_text = "Executado sem ponto de restauração — risco aceito pelo operador"
    else:
        protecao_text = prot.get("mensagem", "Não tentado")

    linhas = [
        "=" * 50,
        "PHOENIX OPTIMIZER - RELATÓRIO TÉCNICO V3",
        "=" * 50,
        f"Cliente: {cliente}",
        f"Atendimento ID: {payload.get('id_atendimento', 'N/D')}",
        f"Data: {payload.get('data_hora', '')}",
        f"Duração: {payload.get('duracao_segundos', 0)}s",
        f"Sistema Operacional: {snapshot_antes.get('sistema', {}).get('sistema', '')} {snapshot_antes.get('sistema', {}).get('versao', '')}",
        f"Processador: {snapshot_antes.get('sistema', {}).get('processador', 'N/D')}",
        f"Memória RAM Total: {snapshot_antes.get('memoria', {}).get('total_gb', 'N/D')} GB",
        "",
        "--- A. RESULTADO DO ATENDIMENTO ---",
        f"Espaço liberado: {resumo.get('espaco_liberado_mb', 0):.2f} MB",
        f"Itens removidos: {resumo.get('itens_removidos', 0)}",
        f"Otimizações aplicadas: {resumo.get('otimizacoes_aplicadas', 0)} de {resumo.get('otimizacoes_total', 0)}",
        f"Status de proteção: {protecao_text}",
        f"Recomendações encontradas: {len(recs)}",
        "",
        "--- B. ACHADOS DO SISTEMA ---",
    ]
    
    # Startup findings
    startup = analises.get("startup", {})
    if startup.get("ok"):
        linhas.append(f"Entradas de inicialização: {startup.get('total', 0)} (Alto impacto: {startup.get('alto_impacto', 0)})")
        
    # Disk Health findings
    smart = analises.get("smart", {})
    if smart.get("ok"):
        discos = smart.get("discos", [])
        for d in discos:
            linhas.append(f"Disco {d.get('device_id')} ({d.get('tipo_midia')}): {d.get('classificacao')}")
            
    linhas.append("")
    linhas.append("--- C. TRABALHO REALIZADO (Otimizações) ---")
    resultados_otim = otim.get("resultados", {})
    before_state = otim.get("before_state", {})
    if not resultados_otim:
        linhas.append("Nenhuma otimização aplicada.")
    else:
        for k, v in resultados_otim.items():
            status = "APLICADO" if v.get("ok") else "FALHOU"
            if before_state and k in before_state:
                item_before = before_state[k]
                is_active_before = item_before.get("ativo", False)
                estado_antes = "Já aplicado" if is_active_before else "Não aplicado"
                linhas.append(f"- {v.get('descricao', k)}")
                linhas.append(f"    Antes: {estado_antes} | Ação: Otimizar | Resultado: {status}")
            else:
                linhas.append(f"- {v.get('descricao', k)} -> {status}")

    cond = payload.get("acoes_condicionais", {})
    if cond.get("otimizacao_disco", {}).get("executado"):
        linhas.append(f"- Otimização de Armazenamento: {cond['otimizacao_disco'].get('saida')}")

    linhas.append("")
    linhas.append("--- D. DETALHES DA LIMPEZA ---")
    categorias = limpeza.get("categorias", [])
    if not categorias:
        linhas.append("Nenhuma categoria processada.")
    else:
        total_removidos = 0
        total_preservados = 0
        for cat in categorias:
            nome = cat.get("nome", "Desconhecido")
            removidos = cat.get("arquivos_removidos", 0)
            ignorados = cat.get("arquivos_ignorados", 0)
            total_removidos += removidos
            total_preservados += ignorados
            mb = cat.get("espaco_liberado_bytes", 0) / (1024*1024)
            status = _formatar_status_limpeza(cat.get("status", ""), ignorados)
            linhas.append(f"- {nome}: {removidos} removidos, {ignorados} preservados, {mb:.2f} MB recuperados [{status}]")
        linhas.append("")
        linhas.append(f"TOTAL: {total_removidos} itens removidos | {total_preservados} itens preservados")

    linhas.append("")
    linhas.append("--- E. SAÚDE DO SISTEMA ---")
    drivers = analises.get("drivers", {})
    if drivers.get("ok") and drivers.get("resultados"):
        linhas.append("Drivers:")
        for dr in drivers.get("resultados", []):
            tipo = "Virtual" if dr.get("virtual") else "Físico"
            linhas.append(f"  - {dr.get('nome')} ({tipo}) [{dr.get('fabricante')}]: {dr.get('classificacao')}")
    else:
        linhas.append("Drivers: Análise indisponível.")

    linhas.append("")
    linhas.append("--- F. ESTADO OBSERVADO (Antes -> Depois) ---")
    linhas.append("Nota: CPU e RAM são medições pontuais e podem variar durante o uso.")
    linhas.append("Isoladamente, essas métricas não representam ganho ou perda de desempenho.")
    linhas.append("")
    try:
        linhas.append(f"Uso de CPU:      {dados_antes['cpu']['uso_percentual']}%  ->  {dados_depois['cpu']['uso_percentual']}%")
        linhas.append(f"Uso de RAM:      {dados_antes['memoria']['percentual_uso']}%  ->  {dados_depois['memoria']['percentual_uso']}%")
        linhas.append(f"RAM disponível:  {dados_antes['memoria']['disponivel_gb']} GB  ->  {dados_depois['memoria']['disponivel_gb']} GB")
        linhas.append("")
        linhas.append("ARMAZENAMENTO:")
        discos_antes = {d["unidade"]: d for d in dados_antes["discos"]}
        discos_depois = {d["unidade"]: d for d in dados_depois["discos"]}
        for unidade, info_antes in discos_antes.items():
            info_depois = discos_depois.get(unidade)
            if info_depois:
                linhas.append(f"{unidade} Livre: {info_antes['livre_gb']} GB  ->  {info_depois['livre_gb']} GB")
    except Exception:
        pass
        
    linhas.append("")
    linhas.append("--- G. RECOMENDAÇÕES ---")
    if not recs:
        linhas.append("Nenhuma recomendação disponível.")
    else:
        for r in recs:
            linhas.append(f"- {r.get('titulo')}: {r.get('descricao')}")

    linhas.append("")
    linhas.append("=" * 50)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


def exportar_relatorio_html(payload: dict, snapshot_antes: dict, snapshot_depois: dict, caminho_saida) -> None:
    """Exporta o relatório técnico V3 em html."""
    import html as html_module

    def escape_safe(val):
        if val is None: return ""
        return html_module.escape(str(val), quote=True)

    dados_antes = snapshot_antes
    dados_depois = snapshot_depois
    cliente = escape_safe(payload.get("cliente", "não informado"))
    
    resumo = payload.get("resumo", {})
    limpeza = payload.get("limpeza", {})
    otim = payload.get("otimizacoes", {})
    prot = payload.get("protecao", {})
    analises = payload.get("analises", {})
    recs = payload.get("recomendacoes", [])
    
    protecao_status = prot.get("status", "N/D")
    if protecao_status == "restore_created":
        protecao_text = "Ponto de restauração criado e verificado"
    elif protecao_status == "risk_accepted":
        protecao_text = "Executado sem ponto de restauração — risco aceito pelo operador"
    else:
        protecao_text = prot.get("mensagem", "Não tentado")

    recs_html = ""
    for r in recs:
        nivel = r.get("nivel", "info")
        color = "#00e676" if nivel == "sucesso" else "#ffb300" if nivel == "aviso" else "#ff1744" if nivel == "erro" else "#00b0ff"
        recs_html += f"<li style='margin-bottom: 10px; border-left: 4px solid {color}; padding-left: 10px;'><strong>{escape_safe(r.get('titulo'))}</strong><br/>{escape_safe(r.get('descricao'))}</li>"

    clean_html = ""
    for cat in limpeza.get("categorias", []):
        nome = escape_safe(cat.get("nome", "Desconhecido"))
        rem = cat.get("arquivos_removidos", 0)
        ign = cat.get("arquivos_ignorados", 0)
        mb = cat.get("espaco_liberado_bytes", 0) / (1024*1024)
        status = _formatar_status_limpeza(cat.get("status", ""), ign)
        badge = "#00e676" if status == "CONCLUÍDO" else "#ffb300" if status == "CONCLUÍDO COM EXCEÇÕES" else "#ff1744" if status == "FALHOU" else "#9e9e9e"
        clean_html += f"<tr><td>{nome}</td><td>{rem}</td><td>{ign}</td><td>{mb:.2f} MB</td><td><span style='background: {badge}; color: #000; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;'>{status}</span></td></tr>"

    otim_html = ""
    for k, v in otim.get("resultados", {}).items():
        desc = escape_safe(v.get("descricao", k))
        status = "APLICADO" if v.get("ok") else "FALHOU"
        otim_html += f"<li>{desc}: <strong>{status}</strong></li>"

    smart_html = ""
    if analises.get("smart", {}).get("ok"):
        for d in analises.get("smart", {}).get("discos", []):
            smart_html += f"<li>Disco {escape_safe(d.get('device_id'))} ({escape_safe(d.get('tipo_midia'))}): {escape_safe(d.get('classificacao'))}</li>"

    drivers_html = ""
    if analises.get("drivers", {}).get("ok"):
        for dr in analises.get("drivers", {}).get("resultados", []):
            tipo = "Virtual" if dr.get("virtual") else "Físico"
            drivers_html += f"<li>{escape_safe(dr.get('nome'))} ({tipo}): {escape_safe(dr.get('classificacao'))}</li>"

    try:
        cpu_antes = f"{dados_antes['cpu']['uso_percentual']}%"
        cpu_depois = f"{dados_depois['cpu']['uso_percentual']}%"
        ram_antes = f"{dados_antes['memoria']['percentual_uso']}%"
        ram_depois = f"{dados_depois['memoria']['percentual_uso']}%"
        ram_disp_antes = f"{dados_antes['memoria']['disponivel_gb']} GB"
        ram_disp_depois = f"{dados_depois['memoria']['disponivel_gb']} GB"
    except Exception:
        cpu_antes = cpu_depois = ram_antes = ram_depois = ram_disp_antes = ram_disp_depois = "N/D"

    discos_html = ""
    try:
        discos_antes = {d["unidade"]: d for d in dados_antes["discos"]}
        discos_depois = {d["unidade"]: d for d in dados_depois["discos"]}
        for unidade, info_antes in discos_antes.items():
            unidade_segura = escape_safe(unidade)
            info_depois = discos_depois.get(unidade)
            if info_depois:
                discos_html += f"<tr><td>{unidade_segura}</td><td>{info_antes['livre_gb']} GB</td><td>{info_depois['livre_gb']} GB</td></tr>"
    except Exception:
        pass

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório Phoenix V3 - {cliente}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: auto; background: #161b22; padding: 30px; border-radius: 8px; border: 1px solid #30363d; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }}
        h1, h2, h3 {{ color: #ff8c00; margin-top: 0; }}
        h1 {{ text-align: center; border-bottom: 1px solid #30363d; padding-bottom: 15px; margin-bottom: 30px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .card {{ background: #21262d; padding: 15px; border-radius: 6px; border: 1px solid #30363d; text-align: center; }}
        .card .title {{ font-size: 12px; color: #8b949e; text-transform: uppercase; margin-bottom: 5px; }}
        .card .value {{ font-size: 24px; font-weight: bold; color: #58a6ff; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #0d1117; }}
        th, td {{ padding: 10px; border: 1px solid #30363d; text-align: left; }}
        th {{ background: #21262d; color: #c9d1d9; }}
        .section {{ margin-bottom: 40px; padding: 20px; background: #21262d; border-radius: 6px; border: 1px solid #30363d; }}
        ul {{ padding-left: 20px; margin: 0; }}
        @media print {{
            body {{ background: #fff; color: #000; }}
            .container {{ border: none; box-shadow: none; padding: 0; }}
            h1, h2, h3 {{ color: #000; }}
            .card {{ border: 1px solid #ccc; background: #f0f0f0; }}
            .card .value {{ color: #000; }}
            .section {{ background: transparent; border: none; padding: 0; margin-bottom: 20px; }}
            table, th, td {{ border: 1px solid #000; background: transparent; color: #000; }}
            th {{ background: #eee; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Phoenix Optimizer<br><small style="color:#8b949e; font-size:16px;">Relatório Técnico V3</small></h1>
        <p><strong>Cliente:</strong> {cliente}<br><strong>Data:</strong> {escape_safe(payload.get('data_hora', ''))}<br><strong>Duração:</strong> {payload.get('duracao_segundos', 0)}s</p>

        <div class="section">
            <h2>A. RESULTADO DO ATENDIMENTO</h2>
            <div class="grid">
                <div class="card">
                    <div class="title">Espaço Recuperado</div>
                    <div class="value">{resumo.get('espaco_liberado_mb', 0):.2f} MB</div>
                </div>
                <div class="card">
                    <div class="title">Itens Removidos</div>
                    <div class="value">{resumo.get('itens_removidos', 0)}</div>
                </div>
                <div class="card">
                    <div class="title">Otimizações</div>
                    <div class="value">{resumo.get('otimizacoes_aplicadas', 0)} / {resumo.get('otimizacoes_total', 0)}</div>
                </div>
                <div class="card">
                    <div class="title">Proteção</div>
                    <div class="value" style="font-size: 14px;">{escape_safe(protecao_text)}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>B. RECOMENDAÇÕES E ESTADO DO SISTEMA</h2>
            <ul style="list-style: none; padding-left: 0;">
                {recs_html if recs_html else "<li>Nenhuma recomendação disponível.</li>"}
            </ul>
            <br>
            <div class="grid">
                <div>
                    <h3>Discos (SMART)</h3>
                    <ul>{smart_html if smart_html else "<li>Não avaliado</li>"}</ul>
                </div>
                <div>
                    <h3>Drivers</h3>
                    <ul>{drivers_html if drivers_html else "<li>Não avaliado</li>"}</ul>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>C. DETALHES DA LIMPEZA E OTIMIZAÇÃO</h2>
            <h3>Otimizações Aplicadas</h3>
            <ul>{otim_html if otim_html else "<li>Nenhuma otimização aplicada.</li>"}</ul>
            <br>
            <h3>Limpeza de Arquivos</h3>
            <table>
                <thead>
                    <tr><th>Categoria</th><th>Removidos</th><th>Preservados</th><th>Liberado</th><th>Status</th></tr>
                </thead>
                <tbody>
                    {clean_html}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>D. OBSERVAÇÃO DO ESTADO (Antes -> Depois)</h2>
            <p style="font-size: 12px; color: #8b949e;">Nota: CPU e RAM são medições pontuais e podem variar durante o uso. Isoladamente, essas métricas não representam ganho ou perda de desempenho.</p>
            <table>
                <thead>
                    <tr><th>Métrica</th><th>Antes</th><th>Depois</th></tr>
                </thead>
                <tbody>
                    <tr><td>Uso de CPU</td><td>{cpu_antes}</td><td>{cpu_depois}</td></tr>
                    <tr><td>Uso de RAM</td><td>{ram_antes}</td><td>{ram_depois}</td></tr>
                    <tr><td>RAM Disponível</td><td>{ram_disp_antes}</td><td>{ram_disp_depois}</td></tr>
                    {discos_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html_content)
