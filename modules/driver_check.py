"""
Módulo de detecção de driver de GPU desatualizado.

Compara a versão do driver instalado (já coletada por hardware.py) com
a versão mais recente disponível, e fornece links de download quando
detecta desatualização.

Funciona para NVIDIA, AMD e Intel — cada fabricante tem sua forma de
consulta e link de download.
"""

from modules.core.windows_command import run_windows_command
import json
import re
from rich.table import Table
from rich.panel import Panel
from rich import box

from modules.shared import console


# Links oficiais de download de driver por fabricante.
# Como não existe API pública universal confiável e estável para todas
# as marcas, o programa aponta para a página de download do fabricante.
LINKS_DOWNLOAD = {
    "NVIDIA": "https://www.nvidia.com/Download/index.aspx",
    "AMD": "https://www.amd.com/pt/support",
    "Intel": "https://www.intel.com.br/content/www/br/pt/support/detect.html",
    "Advanced Micro Devices, Inc.": "https://www.amd.com/pt/support",
    "Intel Corporation": "https://www.intel.com.br/content/www/br/pt/support/detect.html",
    "NVIDIA Corporation": "https://www.nvidia.com/Download/index.aspx",
}


def _consultar_versao_driver_nvidia(cancel_event=None) -> str | None:
    """
    Consulta a versão do driver NVIDIA instalado via nvidia-smi.
    Retorna a versão no formato 'xxx.xx' (ex: '560.94').
    """
    resultado = run_windows_command(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
        operation_name="Consultar driver NVIDIA",
        timeout_seconds=10.0,
        cancel_event=cancel_event
    )
    if resultado.ok:
        versao = resultado.stdout.strip().split("\n")[0].strip()
        if versao:
            return versao
    return None


def _consultar_drivers_wmi(cancel_event=None) -> list:
    """
    Consulta informações de driver de GPU via WMI (funciona para qualquer
    fabricante: NVIDIA, AMD, Intel).
    """
    comando_ps = (
        "Get-CimInstance Win32_VideoController | "
        "Select-Object Name, DriverVersion, DriverDate, AdapterCompatibility, "
        "Status, VideoProcessor | ConvertTo-Json"
    )
    resultado = run_windows_command(
        ["powershell", "-NoProfile", "-Command", comando_ps],
        operation_name="Consultar WMI",
        timeout_seconds=15.0,
        cancel_event=cancel_event
    )
    if resultado.ok:
        saida = resultado.stdout.strip()
        if not saida:
            return []
        try:
            dados = json.loads(saida)
            if isinstance(dados, dict):
                dados = [dados]
            return dados
        except Exception:
            return []
    return []


def _parse_driver_date(data_raw) -> str:
    """
    Converte a data do driver de vários formatos para algo legível.
    O WMI pode retornar a data como string ISO ou como timestamp.
    """
    if data_raw is None:
        return "Desconhecido"
    data_str = str(data_raw)

    # Formato: /Date(timestamp)/  (JSON serializado de .NET DateTime)
    match = re.search(r'/Date\((\d+)\)', data_str)
    if match:
        from datetime import datetime
        timestamp_ms = int(match.group(1))
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%d/%m/%Y")

    # Formato: YYYYMMDD
    if len(data_str) >= 8 and data_str[:8].isdigit():
        return f"{data_str[6:8]}/{data_str[4:6]}/{data_str[:4]}"

    # Formato ISO ou similar
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_str[:10] if len(data_str) > 10 else data_str


def _calcular_idade_driver_dias(data_raw) -> int | None:
    """Calcula quantos dias se passaram desde a data do driver."""
    if data_raw is None:
        return None

    data_str = str(data_raw)
    from datetime import datetime

    dt = None

    # Formato: /Date(timestamp)/
    match = re.search(r'/Date\((\d+)\)', data_str)
    if match:
        timestamp_ms = int(match.group(1))
        dt = datetime.fromtimestamp(timestamp_ms / 1000)

    # Formato YYYYMMDD
    if dt is None and len(data_str) >= 8 and data_str[:8].isdigit():
        try:
            dt = datetime.strptime(data_str[:8], "%Y%m%d")
        except Exception:
            pass

    # Formato ISO
    if dt is None:
        try:
            dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
        except Exception:
            pass

    if dt is None:
        return None

    # Garantir que não é timezone-aware
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    return (datetime.now() - dt).days


def is_virtual_adapter(name: str, manufacturer: str) -> bool:
    """Detects virtual/software display adapters based on common indicators."""
    indicators = ["virtual", "remote", "parsec", "citrix", "vmware", "hyper-v"]
    combined = f"{name} {manufacturer}".lower()
    return any(ind in combined for ind in indicators)


def _classificar_driver(idade_dias: int | None, tipo_adaptador: str = "fisico") -> tuple:
    """
    Classifica o driver com base na sua idade e tipo de adaptador:
    - Adaptador virtual: ignora a idade
    - < 90 dias: Atualizado
    - 90-365 dias: Pode estar desatualizado
    - > 365 dias: Desatualizado
    """
    if tipo_adaptador == "virtual":
        return "Adaptador virtual", "dim", "Adaptador virtual — atualização não avaliada"
    if idade_dias is None:
        return "Desconhecido", "dim", "Não foi possível determinar a data do driver."

    if idade_dias < 90:
        return "Atualizado", "green", "Driver recente (menos de 3 meses)."
    elif idade_dias < 365:
        return "Pode estar desatualizado", "yellow", f"Driver com {idade_dias} dias. Considere verificar se há atualização."
    else:
        meses = idade_dias // 30
        return "Desatualizado", "red", f"Driver com {meses} meses de idade! Recomendamos atualizar."


def verificar_drivers_gpu(cancel_event=None) -> list:
    """
    Verifica o status de atualização de todos os drivers de GPU instalados.
    Retorna uma lista de dicts com os dados de cada GPU.
    """
    gpus_wmi = _consultar_drivers_wmi(cancel_event=cancel_event)
    versao_nvidia = _consultar_versao_driver_nvidia(cancel_event=cancel_event)
    resultados = []

    for gpu in gpus_wmi:
        nome = gpu.get("Name", "GPU desconhecida")
        fabricante = gpu.get("AdapterCompatibility", "Desconhecido")
        versao_driver = gpu.get("DriverVersion", "Desconhecido")
        data_driver_raw = gpu.get("DriverDate")

        # Para NVIDIA, usar a versão do nvidia-smi se disponível (mais precisa)
        if versao_nvidia and ("NVIDIA" in nome.upper() or "NVIDIA" in str(fabricante).upper()):
            versao_driver = versao_nvidia

        data_driver = _parse_driver_date(data_driver_raw)
        idade_dias = _calcular_idade_driver_dias(data_driver_raw)
        tipo_adaptador = "virtual" if is_virtual_adapter(nome, str(fabricante)) else "fisico"
        classificacao, cor, mensagem = _classificar_driver(idade_dias, tipo_adaptador)

        link_download = LINKS_DOWNLOAD.get(fabricante, "")
        if not link_download and tipo_adaptador != "virtual":
            # Tentar por nome parcial
            for chave, url in LINKS_DOWNLOAD.items():
                if chave.upper() in str(fabricante).upper() or chave.upper() in nome.upper():
                    link_download = url
                    break

        resultados.append({
            "nome": nome,
            "fabricante": fabricante,
            "versao_driver": str(versao_driver),
            "data_driver": data_driver,
            "idade_dias": idade_dias,
            "tipo_adaptador": tipo_adaptador,
            "classificacao": classificacao,
            "cor": cor,
            "mensagem": mensagem,
            "link_download": link_download,
        })

    return resultados


def executar_verificacao_drivers(id_atendimento: str = None, cancel_event=None) -> dict:
    """Executa a verificação de drivers e exibe o resultado formatado no terminal."""
    console.print(Panel(
        "[bold yellow]Verificando drivers de GPU...[/bold yellow]",
        border_style="orange3"
    ))

    resultados = verificar_drivers_gpu(cancel_event=cancel_event)

    if not resultados:
        console.print(Panel(
            "[yellow]Nenhuma GPU detectada para verificação de driver.[/yellow]",
            border_style="yellow"
        ))
        return {"ok": True, "itens": []}

    for gpu in resultados:
        tabela = Table(
            title=f"GPU: {gpu['nome']}",
            box=box.ROUNDED,
            border_style=gpu["cor"]
        )
        tabela.add_column("Item", style="bold white")
        tabela.add_column("Valor")

        tabela.add_row("Fabricante", gpu["fabricante"])
        tabela.add_row("Versão do driver", gpu["versao_driver"])
        tabela.add_row("Data do driver", gpu["data_driver"])

        classificacao = gpu["classificacao"]
        cor = gpu["cor"]
        tabela.add_row("Status", f"[bold {cor}]{classificacao}[/bold {cor}]")

        console.print(tabela)
        console.print(f"  [{cor}]→[/{cor}] {gpu['mensagem']}")

        if gpu["link_download"] and classificacao != "Atualizado":
            console.print(f"  [bold blue]↗ Download:[/bold blue] {gpu['link_download']}")

        console.print()

    # Resumo
    desatualizados = sum(1 for g in resultados if g["classificacao"] == "Desatualizado")
    possiveis = sum(1 for g in resultados if g["classificacao"] == "Pode estar desatualizado")
    virtuais = sum(1 for g in resultados if g.get("tipo_adaptador") == "virtual")

    if desatualizados > 0:
        console.print(Panel(
            f"[bold red][AVISO] {desatualizados} driver(s) desatualizado(s) detectado(s).[/bold red]",
            border_style="red"
        ))
    elif possiveis > 0:
        console.print(Panel(
            f"[bold yellow][AVISO] {possiveis} driver(s) podem estar desatualizados. "
            f"Verifique nos links acima.[/bold yellow]",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[bold green][OK] Nenhum driver físico de GPU requer revisão.[/bold green]",
            border_style="green"
        ))

    if virtuais > 0:
        console.print(f"  [dim]{virtuais} adaptador(es) virtual(is) não foram avaliados para atualização.[/dim]")

    if id_atendimento:
        from modules import logs
        resumo = ", ".join(
            f"{g['nome']}: {g['classificacao']} (v{g['versao_driver']})" for g in resultados
        )
        logs.registrar_acao(id_atendimento, "Verificação de drivers GPU", resumo)

    return {"ok": True, "itens": resultados}


if __name__ == "__main__":
    executar_verificacao_drivers()
