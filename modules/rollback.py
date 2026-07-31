"""
Módulo de rollback: salva o estado atual das configurações do Windows
antes de aplicar otimizações e permite restaurá-las depois.

Funciona independentemente do Ponto de Restauração do Windows — o backup
é um simples arquivo JSON com os valores de registro que o programa alterou.
"""

import json
from modules.core.windows_command import run_windows_command
from datetime import datetime
from pathlib import Path
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich import box

from modules.shared import console


# Chaves de registro que o Phoenix Optimizer altera durante otimizações.
# Cada entrada: (caminho_registro, nome_valor, tipo_dado)
CHAVES_RASTREADAS = {
    "plano_energia": {
        "descricao": "Plano de energia ativo",
        "tipo": "powercfg",
    },
    "efeitos_visuais": {
        "descricao": "Preferências de efeitos visuais",
        "caminho": r"HKCU:\Control Panel\Desktop",
        "valor": "UserPreferencesMask",
        "tipo": "registro_binario",
    },
    "apps_segundo_plano": {
        "descricao": "Apps em segundo plano",
        "caminho": r"HKCU:\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
        "valor": "GlobalUserDisabled",
        "tipo": "registro_dword",
    },
    "modo_jogo": {
        "descricao": "Modo de Jogo do Windows",
        "caminho": r"HKCU:\Software\Microsoft\GameBar",
        "valor": "AllowAutoGameMode",
        "tipo": "registro_dword",
    },
    "modo_jogo_auto": {
        "descricao": "Modo de Jogo automático",
        "caminho": r"HKCU:\Software\Microsoft\GameBar",
        "valor": "AutoGameModeEnabled",
        "tipo": "registro_dword",
    },
    "gamebar_overlay": {
        "descricao": "Overlay do Xbox Game Bar",
        "caminho": r"HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR",
        "valor": "AppCaptureEnabled",
        "tipo": "registro_dword",
    },
    "gpu_scheduling": {
        "descricao": "Agendador de GPU por hardware",
        "caminho": r"HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        "valor": "HwSchMode",
        "tipo": "registro_dword",
    },
}


def _obter_pasta_backups() -> Path:
    """Retorna a pasta onde os backups de rollback são salvos."""
    import os
    import sys
    if sys.platform == "win32":
        base = Path(os.environ.get("PROGRAMDATA", Path.home())) / "PhoenixOptimizer"
    else:
        base = Path(__file__).resolve().parent.parent

    pasta = base / "backups"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _ler_valor_registro(caminho: str, nome_valor: str) -> str | None:
    """Lê um valor do registro do Windows via PowerShell."""
    comando_ps = (
        f"try {{ "
        f"(Get-ItemProperty -Path '{caminho}' -Name '{nome_valor}' -ErrorAction Stop).'{nome_valor}' "
        f"}} catch {{ Write-Output 'NOT_FOUND' }}"
    )
    resultado = run_windows_command(
        ["powershell", "-NoProfile", "-Command", comando_ps],
        operation_name=f"Ler {nome_valor}", timeout_seconds=10.0
    )
    if resultado.ok:
        saida = resultado.stdout.strip()
        if saida == "NOT_FOUND" or not saida:
            return None
        return saida
    return None


def _ler_valor_registro_binario(caminho: str, nome_valor: str) -> str | None:
    """Lê um valor binário do registro e retorna como string de bytes."""
    comando_ps = (
        f"try {{ "
        f"$val = (Get-ItemProperty -Path '{caminho}' -Name '{nome_valor}' -ErrorAction Stop).'{nome_valor}'; "
        f"($val | ForEach-Object {{ $_.ToString() }}) -join ',' "
        f"}} catch {{ Write-Output 'NOT_FOUND' }}"
    )
    resultado = run_windows_command(
        ["powershell", "-NoProfile", "-Command", comando_ps],
        operation_name=f"Ler binário {nome_valor}", timeout_seconds=10.0
    )
    if resultado.ok:
        saida = resultado.stdout.strip()
        if saida == "NOT_FOUND" or not saida:
            return None
        return saida
    return None


def _ler_plano_energia_ativo() -> str | None:
    """Retorna o GUID do plano de energia ativo."""
    resultado = run_windows_command(
        ["powercfg", "/getactivescheme"],
        operation_name="Ler plano de energia", timeout_seconds=10.0
    )
    if resultado.ok:
        saida = resultado.stdout.strip()
        if "GUID:" in saida:
            partes = saida.split("GUID:")
            guid = partes[1].strip().split()[0].strip()
            return guid
    return None


def salvar_backup_pre_otimizacao() -> dict:
    """
    Captura o estado atual de todas as configurações que serão alteradas
    e salva em um arquivo JSON. Retorna o resultado da operação.
    """
    console.print("  [dim]Salvando estado atual das configurações para possível rollback...[/dim]")

    backup = {
        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "valores": {},
    }

    for chave_id, config in CHAVES_RASTREADAS.items():
        tipo = config["tipo"]
        valor = None

        if tipo == "powercfg":
            valor = _ler_plano_energia_ativo()
        elif tipo == "registro_dword":
            valor = _ler_valor_registro(config["caminho"], config["valor"])
        elif tipo == "registro_binario":
            valor = _ler_valor_registro_binario(config["caminho"], config["valor"])

        backup["valores"][chave_id] = {
            "descricao": config["descricao"],
            "valor_original": valor,
            "tipo": tipo,
        }

    pasta = _obter_pasta_backups()
    nome_arquivo = f"backup_{backup['timestamp']}.json"
    caminho = pasta / nome_arquivo

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)

    console.print(f"  [green]✓[/green] Backup salvo: {caminho.name}")

    return {"ok": True, "caminho": str(caminho), "timestamp": backup["timestamp"]}


def listar_backups() -> list:
    """Lista todos os backups de rollback disponíveis, do mais recente ao mais antigo."""
    pasta = _obter_pasta_backups()
    backups = []

    for arquivo in sorted(pasta.glob("backup_*.json"), reverse=True):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            backups.append({
                "arquivo": arquivo.name,
                "caminho": str(arquivo),
                "data_hora": dados.get("data_hora", "Desconhecido"),
                "timestamp": dados.get("timestamp", ""),
                "num_valores": len(dados.get("valores", {})),
            })
        except Exception:
            continue

    return backups


def _restaurar_valor_registro(caminho: str, nome_valor: str, valor: str, tipo: str) -> bool:
    """Restaura um valor no registro do Windows."""
    if tipo == "registro_dword":
        comando_ps = (
            f"New-ItemProperty -Path '{caminho}' -Name '{nome_valor}' "
            f"-PropertyType DWord -Value {valor} -Force | Out-Null"
        )
    elif tipo == "registro_binario":
        # valor é uma string "x,y,z" — converter para array de bytes
        comando_ps = (
            f"$bytes = @({valor}); "
            f"Set-ItemProperty -Path '{caminho}' -Name '{nome_valor}' -Value ([byte[]]$bytes) -Force"
        )
    else:
        return False

    resultado = run_windows_command(
        ["powershell", "-NoProfile", "-Command", comando_ps],
        operation_name=f"Restaurar {nome_valor}", timeout_seconds=15.0
    )
    return resultado.ok


def _restaurar_plano_energia(guid: str) -> bool:
    """Restaura o plano de energia original."""
    resultado = run_windows_command(
        ["powercfg", "/setactive", guid],
        operation_name="Restaurar plano de energia", timeout_seconds=10.0
    )
    return resultado.ok


def executar_rollback(caminho_backup: str = None) -> dict:
    """
    Restaura as configurações de um backup específico.
    Se caminho_backup não for informado, usa o backup mais recente.
    """
    if caminho_backup is None:
        backups = listar_backups()
        if not backups:
            return {"ok": False, "erro": "Nenhum backup encontrado para restauração."}
        caminho_backup = backups[0]["caminho"]

    try:
        with open(caminho_backup, "r", encoding="utf-8") as f:
            backup = json.load(f)
    except Exception as e:
        return {"ok": False, "erro": f"Falha ao ler backup: {e}"}

    console.print(Panel(
        f"[bold yellow]Restaurando configurações do backup de {backup['data_hora']}...[/bold yellow]",
        border_style="orange3"
    ))

    restaurados = 0
    pulados = 0
    falhas = 0

    for chave_id, info in backup.get("valores", {}).items():
        valor_original = info.get("valor_original")
        tipo = info.get("tipo", "")
        descricao = info.get("descricao", chave_id)

        if valor_original is None:
            console.print(f"  [dim]–[/dim] {descricao}: [dim]valor original não capturado, pulando[/dim]")
            pulados += 1
            continue

        config = CHAVES_RASTREADAS.get(chave_id)
        if not config:
            pulados += 1
            continue

        sucesso = False
        if tipo == "powercfg":
            sucesso = _restaurar_plano_energia(valor_original)
        elif tipo in ("registro_dword", "registro_binario"):
            sucesso = _restaurar_valor_registro(
                config["caminho"], config["valor"], valor_original, tipo
            )

        if sucesso:
            console.print(f"  [green]✓[/green] {descricao}: restaurado")
            restaurados += 1
        else:
            console.print(f"  [red]✗[/red] {descricao}: falha ao restaurar")
            falhas += 1

    if falhas == 0:
        console.print(Panel(
            f"[bold green]Rollback concluído! {restaurados} configuração(ões) restaurada(s).[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]Rollback parcial: {restaurados} OK, {falhas} falha(s), {pulados} pulado(s).[/bold yellow]",
            border_style="yellow"
        ))

    return {
        "ok": falhas == 0,
        "restaurados": restaurados,
        "falhas": falhas,
        "pulados": pulados,
    }


def exibir_backups_disponiveis():
    """Exibe uma tabela com os backups disponíveis para rollback."""
    backups = listar_backups()

    if not backups:
        console.print(Panel(
            "[yellow]Nenhum backup de otimização encontrado.[/yellow]\n"
            "[dim]Backups são criados automaticamente antes de aplicar otimizações.[/dim]",
            border_style="yellow"
        ))
        return

    tabela = Table(title="Backups Disponíveis", box=box.ROUNDED, border_style="orange3")
    tabela.add_column("#", style="dim")
    tabela.add_column("Data/Hora", style="bold white")
    tabela.add_column("Configurações salvas", style="yellow")

    for i, bk in enumerate(backups, start=1):
        tabela.add_row(str(i), bk["data_hora"], str(bk["num_valores"]))

    console.print(tabela)


def menu_rollback():
    """Menu interativo para o usuário escolher qual backup restaurar."""
    exibir_backups_disponiveis()

    backups = listar_backups()
    if not backups:
        return

    console.print()
    if not Confirm.ask("[bold]Deseja restaurar um backup?[/bold]", default=False):
        return

    if len(backups) == 1:
        escolha = 1
    else:
        numero = console.input(
            "\n[bold white]Digite o número do backup a restaurar (padrão: 1 = mais recente): [/bold white]"
        ).strip()
        try:
            escolha = int(numero) if numero else 1
        except ValueError:
            console.print("[red]Número inválido.[/red]")
            return

    if 1 <= escolha <= len(backups):
        backup_escolhido = backups[escolha - 1]
        executar_rollback(backup_escolhido["caminho"])
    else:
        console.print("[red]Número fora do intervalo.[/red]")


if __name__ == "__main__":
    menu_rollback()
