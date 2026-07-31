"""
Módulo de verificação de saúde de disco (S.M.A.R.T.)

Consulta dados S.M.A.R.T. via WMI/PowerShell nativo do Windows 10/11,
sem dependências externas. Classifica a saúde do disco em:
Saudável / Atenção / Crítico — e exibe alertas visuais no terminal.
"""

from modules.core.windows_command import run_windows_command
import json
from rich.table import Table
from rich.panel import Panel
from rich import box

from modules.shared import console


def _consultar_discos_fisicos() -> list:
    """
    Consulta informações básicas dos discos físicos via PowerShell.
    Retorna modelo, tipo de mídia (SSD/HDD), tamanho e status de saúde.
    """
    comando_ps = (
        "Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, "
        "Size, HealthStatus, OperationalStatus | ConvertTo-Json"
    )
    resultado = run_windows_command(
        ["powershell", "-NoProfile", "-Command", comando_ps],
        operation_name="Consultar discos físicos",
        timeout_seconds=15.0
    )
    if resultado.ok:
        saida = resultado.stdout.strip()
        if not saida:
            return []
        try:
            dados = __import__('json').loads(saida)
            if isinstance(dados, dict):
                dados = [dados]
            return dados
        except Exception:
            return []
    return []


def _consultar_confiabilidade_disco(device_id: str) -> dict | None:
    """
    Consulta contadores de confiabilidade do disco (S.M.A.R.T.) via
    Get-StorageReliabilityCounter. Inclui temperatura, horas de uso,
    setores realocados, erros de leitura/escrita, etc.
    """
    try:
        normalized_device_id = str(int(device_id))
    except (TypeError, ValueError):
        return None

    comando_ps = (
        f"Get-PhysicalDisk | Where-Object DeviceId -eq '{normalized_device_id}' | "
        "Get-StorageReliabilityCounter | Select-Object "
        "Temperature, PowerOnHours, ReadErrorsTotal, WriteErrorsTotal, "
        "ReadErrorsCorrected, WriteErrorsCorrected, Wear | ConvertTo-Json"
    )
    resultado = run_windows_command(
        ["powershell", "-NoProfile", "-Command", comando_ps],
        operation_name=f"Consultar S.M.A.R.T. disco {normalized_device_id}",
        timeout_seconds=15.0
    )
    if resultado.ok:
        saida = resultado.stdout.strip()
        if not saida:
            return None
        try:
            dados = __import__('json').loads(saida)
            if isinstance(dados, list):
                dados = dados[0] if dados else None
            return dados
        except Exception:
            return None
    return None


def classificar_saude(disco_info: dict, confiabilidade: dict | None) -> tuple:
    """
    Classifica a saúde do disco em ('Saudável', 'green'), ('Atenção', 'yellow')
    ou ('Crítico', 'red') com base nos dados coletados.

    Retorna: (classificação, cor, lista_de_alertas)
    """
    alertas = []
    health_status = disco_info.get("HealthStatus", "").lower()
    op_status = disco_info.get("OperationalStatus", "")

    # Classificação primária pelo HealthStatus do Windows
    if health_status == "healthy":
        classificacao = "Saudável"
        cor = "green"
    elif health_status == "warning":
        classificacao = "Atenção"
        cor = "yellow"
        alertas.append("Windows reportou status 'Warning' para este disco")
    else:
        classificacao = "Crítico"
        cor = "red"
        alertas.append(f"Windows reportou status '{health_status}' para este disco")

    if confiabilidade:
        # Temperatura elevada
        temp = confiabilidade.get("Temperature")
        if temp is not None and temp > 0:
            if temp >= 60:
                classificacao = "Crítico"
                cor = "red"
                alertas.append(f"Temperatura crítica: {temp}°C (limite seguro: ~55°C)")
            elif temp >= 50:
                if classificacao == "Saudável":
                    classificacao = "Atenção"
                    cor = "yellow"
                alertas.append(f"Temperatura elevada: {temp}°C (recomendado: <50°C)")

        # Wear leveling (SSD) — percentual de desgaste
        wear = confiabilidade.get("Wear")
        if wear is not None and wear > 0:
            if wear >= 90:
                classificacao = "Crítico"
                cor = "red"
                alertas.append(f"Desgaste do SSD: {wear}% (vida útil quase esgotada!)")
            elif wear >= 70:
                if classificacao == "Saudável":
                    classificacao = "Atenção"
                    cor = "yellow"
                alertas.append(f"Desgaste do SSD: {wear}% (considere substituição em breve)")

        # Erros de leitura/escrita
        erros_leitura = confiabilidade.get("ReadErrorsTotal") or 0
        erros_escrita = confiabilidade.get("WriteErrorsTotal") or 0
        total_erros = erros_leitura + erros_escrita

        if total_erros > 100:
            classificacao = "Crítico"
            cor = "red"
            alertas.append(f"Alto número de erros de I/O: {total_erros} (leitura: {erros_leitura}, escrita: {erros_escrita})")
        elif total_erros > 10:
            if classificacao == "Saudável":
                classificacao = "Atenção"
                cor = "yellow"
            alertas.append(f"Erros de I/O detectados: {total_erros} (leitura: {erros_leitura}, escrita: {erros_escrita})")

        # Horas de uso excessivas (HDD > 40.000h, SSD > 30.000h)
        horas = confiabilidade.get("PowerOnHours")
        tipo_midia = disco_info.get("MediaType", "")
        if horas is not None and horas > 0:
            limite = 30000 if "SSD" in str(tipo_midia) else 40000
            if horas > limite:
                if classificacao == "Saudável":
                    classificacao = "Atenção"
                    cor = "yellow"
                alertas.append(f"Disco com {horas:,} horas de uso (acima da média de vida útil)")

    return classificacao, cor, alertas


def _bytes_para_gb(valor: int) -> float:
    return round(valor / (1024 ** 3), 1) if valor else 0


def coletar_saude_discos() -> list:
    """
    Coleta e retorna as informações de saúde de todos os discos físicos.
    Retorna uma lista de dicts com todos os dados necessários para exibição.
    """
    discos = _consultar_discos_fisicos()
    resultados = []

    for disco in discos:
        device_id = str(disco.get("DeviceId", ""))
        confiabilidade = _consultar_confiabilidade_disco(device_id)
        classificacao, cor, alertas = classificar_saude(disco, confiabilidade)

        info = {
            "device_id": device_id,
            "nome": disco.get("FriendlyName", "Disco desconhecido"),
            "tipo_midia": str(disco.get("MediaType", "Desconhecido")),
            "tamanho_gb": _bytes_para_gb(disco.get("Size", 0)),
            "health_status": disco.get("HealthStatus", "Desconhecido"),
            "classificacao": classificacao,
            "cor": cor,
            "alertas": alertas,
            "confiabilidade": {},
        }

        if confiabilidade:
            info["confiabilidade"] = {
                "temperatura_c": confiabilidade.get("Temperature"),
                "horas_uso": confiabilidade.get("PowerOnHours"),
                "wear_percent": confiabilidade.get("Wear"),
                "erros_leitura": confiabilidade.get("ReadErrorsTotal"),
                "erros_escrita": confiabilidade.get("WriteErrorsTotal"),
            }

        resultados.append(info)

    return resultados


def executar_verificacao_smart(id_atendimento: str = None) -> list:
    """Executa a verificação S.M.A.R.T. completa e exibe relatório formatado no terminal."""
    console.print(Panel(
        "[bold yellow]Verificando saúde dos discos (S.M.A.R.T.)...[/bold yellow]",
        border_style="orange3"
    ))

    resultados = coletar_saude_discos()

    if not resultados:
        console.print(Panel(
            "[yellow]Não foi possível consultar os dados S.M.A.R.T. dos discos.[/yellow]\n"
            "[dim]Isso pode ocorrer se o Windows não expõe os contadores de confiabilidade "
            "para o tipo de disco instalado.[/dim]",
            border_style="yellow"
        ))
        return []

    for disco in resultados:
        tabela = Table(
            title=f"Disco: {disco['nome']}",
            box=box.ROUNDED,
            border_style=disco["cor"]
        )
        tabela.add_column("Item", style="bold white")
        tabela.add_column("Valor")

        tabela.add_row("Tipo", disco["tipo_midia"])
        tabela.add_row("Tamanho", f"{disco['tamanho_gb']} GB")
        tabela.add_row("Status Windows", disco["health_status"])

        conf = disco.get("confiabilidade", {})
        if conf.get("temperatura_c") is not None and conf["temperatura_c"] > 0:
            tabela.add_row("Temperatura", f"{conf['temperatura_c']}°C")
        if conf.get("horas_uso") is not None and conf["horas_uso"] > 0:
            tabela.add_row("Horas de uso", f"{conf['horas_uso']:,}")
        if conf.get("wear_percent") is not None and conf["wear_percent"] > 0:
            tabela.add_row("Desgaste (SSD)", f"{conf['wear_percent']}%")
        if conf.get("erros_leitura") is not None and conf["erros_leitura"] > 0:
            tabela.add_row("Erros de leitura", str(conf["erros_leitura"]))
        if conf.get("erros_escrita") is not None and conf["erros_escrita"] > 0:
            tabela.add_row("Erros de escrita", str(conf["erros_escrita"]))

        classificacao = disco["classificacao"]
        cor = disco["cor"]
        tabela.add_row("Saúde geral", f"[bold {cor}]{classificacao}[/bold {cor}]")

        console.print(tabela)

        # Exibir alertas, se houver
        for alerta in disco.get("alertas", []):
            console.print(f"  [bold {cor}]⚠[/bold {cor}] {alerta}")

        console.print()

    # Resumo final
    criticos = sum(1 for d in resultados if d["classificacao"] == "Crítico")
    atencao = sum(1 for d in resultados if d["classificacao"] == "Atenção")

    if criticos > 0:
        console.print(Panel(
            f"[bold red]⚠ {criticos} disco(s) em estado CRÍTICO! Faça backup dos dados imediatamente.[/bold red]",
            border_style="red"
        ))
    elif atencao > 0:
        console.print(Panel(
            f"[bold yellow]⚠ {atencao} disco(s) requerem atenção. Monitore regularmente.[/bold yellow]",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[bold green]✓ Todos os discos estão saudáveis![/bold green]",
            border_style="green"
        ))

    if id_atendimento:
        from modules import logs
        resumo_discos = ", ".join(
            f"{d['nome']}: {d['classificacao']}" for d in resultados
        )
        logs.registrar_acao(id_atendimento, "Verificação S.M.A.R.T.", resumo_discos)

    return resultados


if __name__ == "__main__":
    executar_verificacao_smart()
