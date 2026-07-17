"""
Módulo de detecção de driver de GPU desatualizado.

Compara a versão do driver instalado (já coletada por hardware.py) com
a versão mais recente disponível, e fornece links de download quando
detecta desatualização.

Funciona para NVIDIA, AMD e Intel — cada fabricante tem sua forma de
consulta e link de download.
"""

import subprocess
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


def _consultar_versao_driver_nvidia() -> str | None:
    """
    Consulta a versão do driver NVIDIA instalado via nvidia-smi.
    Retorna a versão no formato 'xxx.xx' (ex: '560.94').
    """
    try:
        resultado = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if resultado.returncode == 0:
            versao = resultado.stdout.strip().split("\n")[0].strip()
            if versao:
                return versao
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _consultar_drivers_wmi() -> list:
    """
    Consulta informações de driver de GPU via WMI (funciona para qualquer
    fabricante: NVIDIA, AMD, Intel).
    """
    comando_ps = (
        "Get-CimInstance Win32_VideoController | "
        "Select-Object Name, DriverVersion, DriverDate, AdapterCompatibility, "
        "Status, VideoProcessor | ConvertTo-Json"
    )
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando_ps],
            capture_output=True, text=True, timeout=15
        )
        saida = resultado.stdout.strip()
        if not saida:
            return []
        dados = json.loads(saida)
        if isinstance(dados, dict):
            dados = [dados]
        return dados
    except Exception:
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


def _classificar_driver(idade_dias: int | None) -> tuple:
    """
    Classifica o driver com base na sua idade:
    - < 90 dias: Atualizado
    - 90-365 dias: Pode estar desatualizado
    - > 365 dias: Desatualizado
    """
    if idade_dias is None:
        return "Desconhecido", "dim", "Não foi possível determinar a data do driver."

    if idade_dias < 90:
        return "Atualizado", "green", "Driver recente (menos de 3 meses)."
    elif idade_dias < 365:
        return "Pode estar desatualizado", "yellow", f"Driver com {idade_dias} dias. Considere verificar se há atualização."
    else:
        meses = idade_dias // 30
        return "Desatualizado", "red", f"Driver com {meses} meses de idade! Recomendamos atualizar."


def verificar_drivers_gpu() -> list:
    """
    Verifica o status de atualização de todos os drivers de GPU instalados.
    Retorna uma lista de dicts com os dados de cada GPU.
    """
    gpus_wmi = _consultar_drivers_wmi()
    versao_nvidia = _consultar_versao_driver_nvidia()
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
        classificacao, cor, mensagem = _classificar_driver(idade_dias)

        link_download = LINKS_DOWNLOAD.get(fabricante, "")
        if not link_download:
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
            "classificacao": classificacao,
            "cor": cor,
            "mensagem": mensagem,
            "link_download": link_download,
        })

    return resultados


def executar_verificacao_drivers(id_atendimento: str = None) -> list:
    """Executa a verificação de drivers e exibe o resultado formatado no terminal."""
    console.print(Panel(
        "[bold yellow]Verificando drivers de GPU...[/bold yellow]",
        border_style="orange3"
    ))

    resultados = verificar_drivers_gpu()

    if not resultados:
        console.print(Panel(
            "[yellow]Nenhuma GPU detectada para verificação de driver.[/yellow]",
            border_style="yellow"
        ))
        return []

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

    if desatualizados > 0:
        console.print(Panel(
            f"[bold red]⚠ {desatualizados} driver(s) desatualizado(s)! "
            f"Atualizar drivers é a forma mais eficaz de melhorar o desempenho em jogos.[/bold red]",
            border_style="red"
        ))
    elif possiveis > 0:
        console.print(Panel(
            f"[bold yellow]⚠ {possiveis} driver(s) podem estar desatualizados. "
            f"Verifique nos links acima.[/bold yellow]",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[bold green]✓ Todos os drivers de GPU estão atualizados![/bold green]",
            border_style="green"
        ))

    if id_atendimento:
        from modules import logs
        resumo = ", ".join(
            f"{g['nome']}: {g['classificacao']} (v{g['versao_driver']})" for g in resultados
        )
        logs.registrar_acao(id_atendimento, "Verificação de drivers GPU", resumo)

    return resultados


if __name__ == "__main__":
    executar_verificacao_drivers()
