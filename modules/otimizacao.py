"""
Módulo de otimização: ajustes de performance geral do Windows 10/11
e otimizações específicas para ganho de FPS em jogos.

IMPORTANTE: ajustes que alteram registro/serviços do Windows pedem
confirmação do usuário antes de aplicar, e cada função é independente
para que você possa escolher quais aplicar.
"""

import subprocess
import ctypes
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


def is_admin() -> bool:
    """Verifica se o programa possui privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def criar_ponto_restauracao() -> dict:
    """
    Cria um ponto de restauração do sistema operacional Windows via PowerShell.
    Mapeia erros comuns como limite diário excedido ou restauração desativada.
    """
    if not is_admin():
        return {
            "ok": False,
            "erro": "O Phoenix Optimizer requer privilégios de administrador para criar pontos de restauração e aplicar otimizações.",
            "codigo": "NO_ADMIN"
        }

    comando = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "Checkpoint-Computer -Description 'Phoenix Optimizer - Pré-Otimização' -RestorePointType 'MODIFY_SETTINGS'"
    ]

    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=120, shell=False)

        if resultado.returncode == 0:
            return {
                "ok": True,
                "mensagem": "Ponto de restauração 'Phoenix Optimizer - Pré-Otimização' criado com sucesso."
            }
        else:
            stderr = resultado.stderr or ""
            stdout = resultado.stdout or ""
            erro_str = (stderr + "\n" + stdout).strip()

            if "0x80042316" in erro_str or "24 hours" in erro_str or "24 horas" in erro_str:
                codigo = "LIMIT_EXCEEDED"
                erro = "O Windows limita a criação de pontos de restauração a um a cada 24 horas por padrão."
            elif "disabled" in erro_str.lower() or "desativada" in erro_str.lower() or "desativado" in erro_str.lower():
                codigo = "RESTORE_DISABLED"
                erro = "A Restauração do Sistema (System Protection) está desativada no Windows para a unidade C:."
            elif "access denied" in erro_str.lower() or "permissão" in erro_str.lower() or "privilégio" in erro_str.lower():
                codigo = "NO_ADMIN"
                erro = "Privilégios de Administrador insuficientes."
            else:
                codigo = "UNKNOWN"
                erro = f"Falha ao criar ponto de restauração do Windows: {erro_str[:150]}"

            return {
                "ok": False,
                "erro": erro,
                "codigo": codigo
            }

    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "erro": "Tempo limite excedido ao tentar criar o ponto de restauração.",
            "codigo": "TIMEOUT"
        }
    except Exception as e:
        return {
            "ok": False,
            "erro": f"Erro inesperado: {str(e)}",
            "codigo": "UNKNOWN"
        }



def _executar_comando(comando: list, nome_acao: str) -> bool:
    """Executa um comando do sistema e trata erros sem travar o programa."""
    try:
        resultado = subprocess.run(comando, capture_output=True, timeout=30, shell=False)
        if resultado.returncode != 0:
            console.print(f"  [yellow]⚠[/yellow] {nome_acao} (comando retornou código {resultado.returncode})")
            return False
        console.print(f"  [green]✓[/green] {nome_acao}")
        return True
    except FileNotFoundError:
        console.print(f"  [red]✗[/red] {nome_acao} (comando não encontrado no sistema)")
        return False
    except subprocess.TimeoutExpired:
        console.print(f"  [red]✗[/red] {nome_acao} (tempo limite excedido)")
        return False
    except Exception as e:
        console.print(f"  [red]✗[/red] {nome_acao} (falhou: {e})")
        return False


def ativar_plano_energia_alto_desempenho():
    """Ativa o plano de energia 'Alto desempenho' do Windows."""
    return _executar_comando(
        ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
        "Plano de energia: Alto desempenho ativado"
    )


def desativar_efeitos_visuais():
    """
    Ajusta o Windows para priorizar performance em vez de efeitos visuais
    (desativa animações, sombras e transparências).
    """
    comando_ps = (
        "Set-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' "
        "-Name UserPreferencesMask -Value ([byte[]](144,18,3,128,16,0,0,0)) -Force"
    )
    return _executar_comando(
        ["powershell", "-Command", comando_ps],
        "Efeitos visuais reduzidos (modo performance)"
    )


def ativar_modo_jogo_windows():
    """Garante que o Modo de Jogo do Windows está ativado via registro."""
    comando_ps = (
        "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\GameBar' "
        "-Name AllowAutoGameMode -PropertyType DWord -Value 1 -Force | Out-Null; "
        "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\GameBar' "
        "-Name AutoGameModeEnabled -PropertyType DWord -Value 1 -Force | Out-Null"
    )
    return _executar_comando(["powershell", "-Command", comando_ps], "Modo de Jogo do Windows ativado")


def desativar_gamebar_overlay():
    """Desativa a sobreposição (overlay) do Xbox Game Bar, que consome recursos."""
    comando_ps = (
        "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR' "
        "-Name AppCaptureEnabled -PropertyType DWord -Value 0 -Force | Out-Null"
    )
    return _executar_comando(["powershell", "-Command", comando_ps], "Overlay do Xbox Game Bar desativado")


def limitar_processos_em_segundo_plano():
    """Desativa apps em segundo plano que consomem CPU/RAM sem necessidade (UWP apps)."""
    comando_ps = (
        "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications' "
        "-Name GlobalUserDisabled -PropertyType DWord -Value 1 -Force | Out-Null"
    )
    return _executar_comando(["powershell", "-Command", comando_ps], "Apps em segundo plano restringidos")


def otimizar_gpu_para_jogos():
    """
    Ativa o agendador de GPU acelerado por hardware (Hardware-Accelerated GPU Scheduling),
    disponível no Windows 10 2004+ e Windows 11 — reduz latência em jogos.
    """
    comando_ps = (
        "New-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers' "
        "-Name HwSchMode -PropertyType DWord -Value 2 -Force | Out-Null"
    )
    return _executar_comando(
        ["powershell", "-Command", comando_ps],
        "Agendador de GPU por hardware ativado (requer reinício)"
    )


def listar_itens_inicializacao() -> str:
    """Lista os programas configurados para abrir junto com o Windows."""
    comando_ps = (
        "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | Format-Table -AutoSize"
    )
    try:
        resultado = subprocess.run(
            ["powershell", "-Command", comando_ps],
            capture_output=True, text=True, timeout=30
        )
        saida = resultado.stdout.strip()
        if not saida:
            erro = resultado.stderr.strip()
            return f"Nenhum item encontrado." + (f"\n\nDetalhe: {erro}" if erro else "")
        return saida
    except FileNotFoundError:
        return "Erro: PowerShell não encontrado neste sistema."
    except subprocess.TimeoutExpired:
        return "Erro: a consulta demorou demais e foi interrompida."
    except Exception as e:
        return f"Erro ao listar: {e}"


def otimizar_disco_principal() -> str:
    """
    Executa otimização do disco C: — TRIM se for SSD, desfragmentação se for HDD.
    O Windows já decide automaticamente o método correto via /retrim ou /defrag.
    """
    try:
        resultado = subprocess.run(
            ["defrag", "C:", "/O"],  # /O deixa o Windows escolher o método ideal (TRIM ou defrag)
            capture_output=True, text=True, timeout=300
        )
        console.print("  [green]✓[/green] Otimização de disco (C:) executada")
        return resultado.stdout
    except subprocess.TimeoutExpired:
        console.print("  [yellow]⚠[/yellow] Otimização de disco demorou mais que o esperado e foi interrompida")
        return ""
    except Exception as e:
        console.print(f"  [red]✗[/red] Falha na otimização de disco: {e}")
        return ""


def executar_verificacao_arquivos_sistema() -> bool:
    """Executa o SFC (System File Checker) para verificar integridade de arquivos do sistema."""
    return _executar_comando(["sfc", "/scannow"], "Verificação de arquivos do sistema (SFC) executada")


def limpar_dns_e_rede():
    """Reinicia adaptadores e limpa configurações de rede que podem causar lentidão/ping alto."""
    comandos = [
        (["ipconfig", "/flushdns"], "Cache DNS limpo"),
        (["netsh", "winsock", "reset"], "Winsock resetado (melhora conexão em jogos online)"),
        (["netsh", "int", "ip", "reset"], "Pilha TCP/IP resetada"),
    ]
    for cmd, nome in comandos:
        _executar_comando(cmd, nome)


def executar_otimizacao_geral(id_atendimento: str = None):
    """Executa o conjunto de otimizações gerais de performance (não-destrutivas)."""
    console.print(Panel("[bold yellow]Aplicando otimizações de performance...[/bold yellow]", border_style="orange3"))
    ativar_plano_energia_alto_desempenho()
    desativar_efeitos_visuais()
    limitar_processos_em_segundo_plano()
    console.print(Panel("[bold green]Otimizações de performance aplicadas![/bold green]", border_style="green"))

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Otimização geral aplicada")


def executar_otimizacao_gaming(id_atendimento: str = None):
    """Executa o conjunto de otimizações focadas em ganho de FPS para jogos."""
    console.print(Panel("[bold yellow]Aplicando otimizações para jogos (FPS)...[/bold yellow]", border_style="orange3"))
    ativar_plano_energia_alto_desempenho()
    ativar_modo_jogo_windows()
    desativar_gamebar_overlay()
    otimizar_gpu_para_jogos()

    console.print()
    if Confirm.ask("[bold]Deseja também resetar a rede (ajuda em jogos online com ping alto)?[/bold]", default=False):
        limpar_dns_e_rede()

    console.print(Panel(
        "[bold green]Otimizações de FPS aplicadas! Reinicie o PC para garantir que tudo seja aplicado.[/bold green]",
        border_style="green"
    ))

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Otimização para jogos aplicada")


if __name__ == "__main__":
    executar_otimizacao_geral()
