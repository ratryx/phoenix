"""
Módulo de diagnóstico: coleta informações reais do PC do cliente
(CPU, memória RAM, disco, processos mais pesados, inicialização).
Funciona em Windows 10 e 11.
"""

import platform
import psutil
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def bytes_para_gb(valor_bytes: int) -> float:
    return round(valor_bytes / (1024 ** 3), 2)


def coletar_info_sistema() -> dict:
    """Coleta dados gerais do sistema operacional."""
    return {
        "sistema": platform.system(),
        "versao": platform.version(),
        "release": platform.release(),
        "arquitetura": platform.machine(),
        "processador": platform.processor(),
    }


def coletar_cpu() -> dict:
    """Coleta uso e informações da CPU."""
    return {
        "uso_percentual": psutil.cpu_percent(interval=1),
        "nucleos_fisicos": psutil.cpu_count(logical=False),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "frequencia_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
    }


def coletar_memoria() -> dict:
    """Coleta uso de memória RAM."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": bytes_para_gb(mem.total),
        "usado_gb": bytes_para_gb(mem.used),
        "disponivel_gb": bytes_para_gb(mem.available),
        "percentual_uso": round(mem.percent, 1),
    }


def coletar_disco() -> list:
    """Coleta uso de cada partição/disco do sistema."""
    discos = []
    for particao in psutil.disk_partitions():
        try:
            uso = psutil.disk_usage(particao.mountpoint)
            discos.append({
                "unidade": particao.device,
                "total_gb": bytes_para_gb(uso.total),
                "usado_gb": bytes_para_gb(uso.used),
                "livre_gb": bytes_para_gb(uso.free),
                "percentual_uso": uso.percent,
            })
        except PermissionError:
            continue
    return discos


def coletar_processos_pesados(limite: int = 8) -> list:
    """Retorna os processos que mais consomem CPU/RAM no momento."""
    processos = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            processos.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processos.sort(key=lambda p: (p.get("cpu_percent") or 0) + (p.get("memory_percent") or 0), reverse=True)
    return processos[:limite]


def coletar_diagnostico_silencioso() -> dict:
    """
    Coleta todos os dados de diagnóstico sem imprimir nada no terminal.
    Usado para gerar snapshots (antes/depois) sem poluir a tela com tabelas repetidas.
    """
    return {
        "sistema": coletar_info_sistema(),
        "cpu": coletar_cpu(),
        "memoria": coletar_memoria(),
        "discos": coletar_disco(),
        "processos": coletar_processos_pesados(),
    }


def executar_diagnostico_completo():
    """Executa o diagnóstico completo e exibe um relatório formatado no terminal."""
    console.print(Panel("[bold yellow]Iniciando diagnóstico do sistema...[/bold yellow]", border_style="orange3"))

    info_sis = coletar_info_sistema()
    cpu = coletar_cpu()
    mem = coletar_memoria()
    discos = coletar_disco()
    processos = coletar_processos_pesados()

    # Tabela: Sistema
    tabela_sis = Table(title="Sistema", box=box.ROUNDED, border_style="orange3")
    tabela_sis.add_column("Item", style="bold white")
    tabela_sis.add_column("Valor", style="yellow")
    tabela_sis.add_row("Sistema Operacional", f"{info_sis['sistema']} {info_sis['release']}")
    tabela_sis.add_row("Versão", info_sis["versao"])
    tabela_sis.add_row("Arquitetura", info_sis["arquitetura"])
    console.print(tabela_sis)

    # Tabela: CPU e Memória
    tabela_recursos = Table(title="CPU & Memória", box=box.ROUNDED, border_style="orange3")
    tabela_recursos.add_column("Item", style="bold white")
    tabela_recursos.add_column("Valor", style="yellow")
    tabela_recursos.add_row("Uso de CPU", f"{cpu['uso_percentual']}%")
    tabela_recursos.add_row("Núcleos (físicos/lógicos)", f"{cpu['nucleos_fisicos']} / {cpu['nucleos_logicos']}")
    tabela_recursos.add_row("RAM Total", f"{mem['total_gb']} GB")
    tabela_recursos.add_row("RAM em Uso", f"{mem['usado_gb']} GB ({mem['percentual_uso']}%)")
    tabela_recursos.add_row("RAM Disponível", f"{mem['disponivel_gb']} GB")
    console.print(tabela_recursos)

    # Tabela: Disco
    tabela_disco = Table(title="Armazenamento", box=box.ROUNDED, border_style="orange3")
    tabela_disco.add_column("Unidade", style="bold white")
    tabela_disco.add_column("Total", style="yellow")
    tabela_disco.add_column("Usado", style="yellow")
    tabela_disco.add_column("Livre", style="green")
    tabela_disco.add_column("Uso %", style="red")
    for d in discos:
        tabela_disco.add_row(
            d["unidade"], f"{d['total_gb']} GB", f"{d['usado_gb']} GB",
            f"{d['livre_gb']} GB", f"{d['percentual_uso']}%"
        )
    console.print(tabela_disco)

    # Tabela: Processos mais pesados
    tabela_proc = Table(title="Top processos (CPU + RAM)", box=box.ROUNDED, border_style="orange3")
    tabela_proc.add_column("PID", style="dim")
    tabela_proc.add_column("Processo", style="bold white")
    tabela_proc.add_column("CPU %", style="red")
    tabela_proc.add_column("RAM %", style="yellow")
    for p in processos:
        tabela_proc.add_row(
            str(p.get("pid", "-")),
            str(p.get("name", "desconhecido")),
            f"{p.get('cpu_percent', 0):.1f}",
            f"{p.get('memory_percent', 0):.1f}",
        )
    console.print(tabela_proc)

    console.print(Panel("[bold green]Diagnóstico concluído![/bold green]", border_style="green"))

    return {
        "sistema": info_sis,
        "cpu": cpu,
        "memoria": mem,
        "discos": discos,
        "processos": processos,
    }


if __name__ == "__main__":
    executar_diagnostico_completo()
