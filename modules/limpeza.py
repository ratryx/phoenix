"""
Módulo de limpeza: remove arquivos temporários, cache e lixo do sistema
no Windows 10/11. Sempre soma o espaço liberado para exibir no relatório final.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from modules.shared import console


def tamanho_pasta(caminho: str) -> int:
    """Calcula o tamanho total de uma pasta em bytes."""
    total = 0
    try:
        for raiz, _, arquivos in os.walk(caminho):
            for nome in arquivos:
                caminho_completo = os.path.join(raiz, nome)
                try:
                    total += os.path.getsize(caminho_completo)
                except (OSError, FileNotFoundError):
                    continue
    except (OSError, FileNotFoundError, PermissionError):
        pass
    return total


def limpar_pasta(caminho: str) -> int:
    """
    Remove o conteúdo de uma pasta (arquivos e subpastas) sem apagar a pasta raiz.
    Retorna a quantidade de bytes liberados. Ignora arquivos em uso/bloqueados.
    """
    liberado = 0
    if not os.path.exists(caminho):
        return 0

    for item in Path(caminho).glob("*"):
        try:
            if item.is_file() or item.is_symlink():
                tamanho = item.stat().st_size
                item.unlink()
                liberado += tamanho
            elif item.is_dir():
                tamanho = tamanho_pasta(str(item))
                shutil.rmtree(item, ignore_errors=True)
                liberado += tamanho
        except (PermissionError, OSError, FileNotFoundError):
            continue  # arquivo em uso pelo sistema, pula sem travar o programa

    return liberado


def limpar_cache_firefox(pasta_profiles: str) -> int:
    """
    Limpa apenas a subpasta 'cache2' dentro de cada perfil do Firefox,
    sem apagar os perfis (que contêm senhas, favoritos, histórico etc).
    """
    liberado = 0
    if not os.path.exists(pasta_profiles):
        return 0

    for perfil in Path(pasta_profiles).glob("*"):
        cache_path = perfil / "cache2"
        if cache_path.exists():
            liberado += limpar_pasta(str(cache_path))

    return liberado


def limpar_lixeira() -> bool:
    """Esvazia a lixeira do Windows usando PowerShell."""
    try:
        subprocess.run(
            ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
            capture_output=True, timeout=30
        )
        return True
    except Exception:
        return False


def limpar_cache_dns() -> bool:
    """Limpa o cache de DNS (útil para resolver lentidão de internet)."""
    try:
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=15)
        return True
    except Exception:
        return False


def bytes_para_mb(valor: int) -> float:
    return round(valor / (1024 ** 2), 2)


def obter_alvos_limpeza() -> dict:
    """Retorna o dicionário completo de pastas que podem ser limpas com segurança."""
    usuario = os.path.expanduser("~")
    local = os.path.join(usuario, "AppData", "Local")
    roaming = os.path.join(usuario, "AppData", "Roaming")

    return {
        "Temp do Windows": tempfile.gettempdir(),
        "Temp do usuário": os.path.join(local, "Temp"),
        "Cache de prefetch": r"C:\Windows\Prefetch",
        "Logs do Windows Update": r"C:\Windows\SoftwareDistribution\Download",
        "Relatórios de erro do Windows": os.path.join(local, "Microsoft", "Windows", "WER"),
        "Cache de miniaturas": os.path.join(local, "Microsoft", "Windows", "Explorer"),
        "Cache do Chrome": os.path.join(local, "Google", "Chrome", "User Data", "Default", "Cache"),
        "Cache do Edge": os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Cache"),
        "Lixo de instaladores (Downloaded Installations)": os.path.join(local, "Temp", "Downloaded Installations"),
        "Cache de fontes do Windows": os.path.join(local, "Microsoft", "Windows", "Fonts"),
        "Dumps de memória (CrashDumps)": os.path.join(local, "CrashDumps"),
    }


def executar_limpeza_completa(id_atendimento: str = None):
    """Executa a limpeza completa do sistema e exibe relatório de espaço liberado."""
    console.print(Panel("[bold yellow]Iniciando limpeza do sistema...[/bold yellow]", border_style="orange3"))

    alvos = obter_alvos_limpeza()

    total_liberado = 0
    resultados = []

    with Progress(
        SpinnerColumn(style="orange3"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(complete_style="orange3"),
        console=console,
    ) as progress:
        tarefa = progress.add_task("Limpando arquivos...", total=len(alvos))

        for nome, caminho in alvos.items():
            progress.update(tarefa, description=f"Limpando: {nome}")
            liberado = limpar_pasta(caminho)
            total_liberado += liberado
            resultados.append((nome, bytes_para_mb(liberado)))
            progress.advance(tarefa)

        usuario = os.path.expanduser("~")
        pasta_firefox = os.path.join(usuario, "AppData", "Local", "Mozilla", "Firefox", "Profiles")
        progress.update(tarefa, description="Limpando: Cache do Firefox")
        liberado_firefox = limpar_cache_firefox(pasta_firefox)
        total_liberado += liberado_firefox
        resultados.append(("Cache do Firefox", bytes_para_mb(liberado_firefox)))

        progress.update(tarefa, description="Esvaziando lixeira...")
        limpar_lixeira()
        progress.advance(tarefa)

        progress.update(tarefa, description="Limpando cache de DNS...")
        limpar_cache_dns()

    console.print()
    for nome, mb in resultados:
        if mb > 0:
            console.print(f"  [green]✓[/green] {nome}: [yellow]{mb} MB[/yellow] liberados")
        else:
            console.print(f"  [dim]–[/dim] {nome}: [dim]nada a limpar[/dim]")

    console.print()
    console.print(Panel(
        f"[bold green]Limpeza concluída! Total liberado: {bytes_para_mb(total_liberado)} MB[/bold green]",
        border_style="green"
    ))

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Limpeza executada", f"{bytes_para_mb(total_liberado)} MB liberados")

    return total_liberado


if __name__ == "__main__":
    executar_limpeza_completa()
