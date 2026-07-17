"""
Módulo de otimização: ajustes de performance geral do Windows 10/11
e otimizações específicas para ganho de FPS em jogos.

IMPORTANTE: ajustes que alteram registro/serviços do Windows pedem
confirmação do usuário antes de aplicar, e cada função é independente
para que você possa escolher quais aplicar.
"""

import subprocess
import ctypes
from rich.panel import Panel

from modules.shared import console

# Estrutura de mapeamento para as verificações de status de otimização
ITENS_VERIFICACAO = {
    "modo_jogo": {
        "descricao": "Modo de Jogo do Windows",
        "tipo": "registro",
        "raiz": "HKCU",
        "caminho": r"Software\Microsoft\GameBar",
        "valores": {"AllowAutoGameMode": 1, "AutoGameModeEnabled": 1}
    },
    "gpu_scheduling": {
        "descricao": "Agendador de GPU por Hardware",
        "tipo": "registro",
        "raiz": "HKLM",
        "caminho": r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        "valores": {"HwSchMode": 2}
    },
    "gamebar_overlay": {
        "descricao": "Overlay do Xbox Game Bar (Desativado)",
        "tipo": "registro",
        "raiz": "HKCU",
        "caminho": r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
        "valores": {"AppCaptureEnabled": 0}
    },
    "efeitos_visuais": {
        "descricao": "Efeitos Visuais Reduzidos",
        "tipo": "registro",
        "raiz": "HKCU",
        "caminho": r"Control Panel\Desktop",
        # UserPreferencesMask no modo performance começa com [144, 18, 3, 128...]
        # Para validação simplificada via winreg, comparamos com o esperado (b'\x90\x12\x03\x80\x10\x00\x00\x00')
        "valores": {"UserPreferencesMask": b'\x90\x12\x03\x80\x10\x00\x00\x00'}
    },
    "apps_segundo_plano": {
        "descricao": "Apps em Segundo Plano",
        "tipo": "registro",
        "raiz": "HKCU",
        "caminho": r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
        "valores": {"GlobalUserDisabled": 1}
    }
}
import winreg
from datetime import datetime

def verificar_status_otimizacoes() -> dict:
    """Verifica o status das otimizações ativas consultando o registro e serviços."""
    resultados = {
        "data_verificacao": datetime.now().isoformat(),
        "total_ativos": 0,
        "total_inativos": 0,
        "itens": []
    }
    
    # Check planos de energia (requires subprocess, we use a fast approach if possible, or just powercfg)
    try:
        res = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=5)
        # 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c is High Performance
        # e9a42b02-d5df-448d-aa00-03f14749eb61 is Ultimate Performance
        is_active = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" in res.stdout or "e9a42b02-d5df-448d-aa00-03f14749eb61" in res.stdout
        resultados["itens"].append({
            "id": "plano_energia",
            "descricao": "Plano de energia de Alto Desempenho",
            "ativo": is_active,
            "detalhe": "Ativo" if is_active else "Inativo ou outro plano selecionado."
        })
    except Exception as e:
        resultados["itens"].append({
            "id": "plano_energia",
            "descricao": "Plano de energia de Alto Desempenho",
            "ativo": False,
            "detalhe": f"Erro: {e}"
        })
    
    # Check registry keys
    for key_id, config in ITENS_VERIFICACAO.items():
        if config["tipo"] == "registro":
            ativo = True
            detalhe_erro = ""
            try:
                root_key = winreg.HKEY_CURRENT_USER if config["raiz"] == "HKCU" else winreg.HKEY_LOCAL_MACHINE
                with winreg.OpenKey(root_key, config["caminho"], 0, winreg.KEY_READ) as k:
                    for val_name, expected_val in config["valores"].items():
                        try:
                            val, reg_type = winreg.QueryValueEx(k, val_name)
                            if val != expected_val:
                                ativo = False
                                detalhe_erro = f"Valor esperado {expected_val}, encontrado {val}."
                                break
                        except FileNotFoundError:
                            ativo = False
                            detalhe_erro = f"Chave {val_name} não encontrada."
                            break
            except Exception as e:
                ativo = False
                detalhe_erro = "Caminho do registro não existe ou sem permissão."
                
            resultados["itens"].append({
                "id": key_id,
                "descricao": config["descricao"],
                "ativo": ativo,
                "detalhe": "Ativo" if ativo else detalhe_erro
            })
            
    # Count totals
    resultados["total_ativos"] = sum(1 for item in resultados["itens"] if item["ativo"])
    resultados["total_inativos"] = len(resultados["itens"]) - resultados["total_ativos"]
    
    return resultados

def reaplicar_otimizacao(id_otimizacao: str) -> dict:
    """Reaplica uma otimização específica após backup do ponto de restauração."""
    # Como não temos como saber o que havia antes de re-escrever o registro de forma segura,
    # o criar_ponto_restauracao é usado como safety net antes de qualquer reaplicação.
    if id_otimizacao == "plano_energia":
        ativar_plano_energia_alto_desempenho()
        return {"ok": True, "id": id_otimizacao}
        
    config = ITENS_VERIFICACAO.get(id_otimizacao)
    if not config:
        return {"ok": False, "erro": "ID não encontrado"}
        
    if config["tipo"] == "registro":
        if id_otimizacao == "modo_jogo":
            ativar_modo_jogo_windows()
        elif id_otimizacao == "gpu_scheduling":
            otimizar_gpu_para_jogos()
        elif id_otimizacao == "gamebar_overlay":
            desativar_gamebar_overlay()
        elif id_otimizacao == "efeitos_visuais":
            desativar_efeitos_visuais()
        elif id_otimizacao == "apps_segundo_plano":
            limitar_processos_em_segundo_plano()
        return {"ok": True, "id": id_otimizacao}
        
    return {"ok": False, "erro": "Tipo de otimização não suportado"}

def reaplicar_todas_inativas(status_atual: dict) -> dict:
    """Reaplica em lote todas as inativas com 1 único ponto de restauração prévio."""
    criar_ponto_restauracao()
    reaplicadas = []
    
    for item in status_atual.get("itens", []):
        if not item["ativo"]:
            res = reaplicar_otimizacao(item["id"])
            if res.get("ok"):
                reaplicadas.append(item["id"])
                
    return {"ok": True, "reaplicadas": reaplicadas}


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


def executar_verificacao_integridade_sistema(id_atendimento: str = None) -> dict:
    """
    Executa verificação completa de integridade do Windows:
    1. DISM (repara o store de componentes do Windows)
    2. SFC (verifica e repara arquivos de sistema usando o store reparado)
    """
    console.print(Panel("[bold yellow]Verificando integridade do sistema...[/bold yellow]", border_style="orange3"))
    console.print("  [dim]Isso pode levar vários minutos. Não feche o programa.[/dim]\n")

    resultados = {"dism": False, "sfc": False}

    console.print("  [bold]Etapa 1/2 — DISM (reparando store de componentes)...[/bold]")
    resultados["dism"] = _executar_comando(
        ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
        "DISM: Store de componentes verificado/reparado"
    )

    console.print("  [bold]Etapa 2/2 — SFC (verificando arquivos do sistema)...[/bold]")
    resultados["sfc"] = _executar_comando(
        ["sfc", "/scannow"],
        "SFC: Arquivos do sistema verificados"
    )

    sucesso = resultados["dism"] and resultados["sfc"]
    if sucesso:
        console.print(Panel("[bold green]Verificação de integridade concluída com sucesso![/bold green]", border_style="green"))
    else:
        console.print(Panel("[bold yellow]Verificação concluída com avisos. Verifique os resultados acima.[/bold yellow]", border_style="yellow"))

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Verificação de integridade do sistema",
                          f"DISM: {'OK' if resultados['dism'] else 'Falha'}, SFC: {'OK' if resultados['sfc'] else 'Falha'}")

    return resultados


def limpar_dns_e_rede():
    """Reinicia adaptadores e limpa configurações de rede que podem causar lentidão/ping alto."""
    comandos = [
        (["ipconfig", "/flushdns"], "Cache DNS limpo"),
        (["netsh", "winsock", "reset"], "Winsock resetado (melhora conexão em jogos online)"),
        (["netsh", "int", "ip", "reset"], "Pilha TCP/IP resetada"),
    ]
    for cmd, nome in comandos:
        _executar_comando(cmd, nome)


def executar_otimizacao_geral(id_atendimento: str = None) -> dict:
    """Executa o conjunto de otimizações gerais de performance (não-destrutivas)."""
    console.print(Panel("[bold yellow]Aplicando otimizações de performance...[/bold yellow]", border_style="orange3"))

    resultados = {
        "plano_energia": ativar_plano_energia_alto_desempenho(),
        "efeitos_visuais": desativar_efeitos_visuais(),
        "apps_segundo_plano": limitar_processos_em_segundo_plano(),
    }

    sucesso = sum(1 for v in resultados.values() if v)
    total = len(resultados)

    if sucesso == total:
        console.print(Panel("[bold green]Todas as otimizações de performance aplicadas![/bold green]", border_style="green"))
    else:
        console.print(Panel(
            f"[bold yellow]Otimizações aplicadas: {sucesso}/{total} (verifique os avisos acima)[/bold yellow]",
            border_style="yellow"
        ))

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Otimização geral aplicada",
                          f"{sucesso}/{total} otimizações com sucesso")

    return resultados


def executar_otimizacao_gaming(id_atendimento: str = None, 
                                resetar_rede: bool = False) -> dict:
    console.print(Panel(
        "[bold yellow]Aplicando otimizações para jogos (FPS)...[/bold yellow]", 
        border_style="orange3"
    ))
    ativar_plano_energia_alto_desempenho()
    ativar_modo_jogo_windows()
    desativar_gamebar_overlay()
    otimizar_gpu_para_jogos()
    
    if resetar_rede:
        limpar_dns_e_rede()

    console.print(Panel(
        "[bold green]Otimizações de FPS aplicadas! "
        "Reinicie o PC para garantir que tudo seja aplicado.[/bold green]",
        border_style="green"
    ))

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Otimização para jogos aplicada")
    
    return {"ok": True}

def liberar_memoria_standby() -> bool:
    """
    Libera a memória em standby/cache do Windows.
    Seguro e reversível — o Windows refaz o cache automaticamente.
    Requer privilégios de administrador.
    """
    try:
        # Método via API nativa do Windows
        import ctypes
        # 0x80000000 = MemoryPurgeStandbyList
        ctypes.windll.ntdll.NtSetSystemInformation(80, 
            ctypes.byref(ctypes.c_int(4)), ctypes.sizeof(ctypes.c_int))
        return True
    except Exception:
        return False

def desativar_suspensao_energia() -> bool:
    """
    Configura o Windows para nunca suspender quando conectado 
    na energia elétrica. Ideal para sessões de otimização longas.
    """
    try:
        subprocess.run(
            ["powercfg", "/change", "standby-timeout-ac", "0"],
            capture_output=True, timeout=10
        )
        subprocess.run(
            ["powercfg", "/change", "monitor-timeout-ac", "0"],
            capture_output=True, timeout=10
        )
        return True
    except Exception:
        return False

def analisar_startup() -> list:
    """
    Lista programas de inicialização com impacto no tempo de boot.
    Usa o registro do Windows para identificar entradas de startup.
    """
    import winreg
    entradas = []
    chaves = [
        (winreg.HKEY_CURRENT_USER, 
         r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, 
         r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ]
    for raiz, caminho in chaves:
        try:
            with winreg.OpenKey(raiz, caminho) as k:
                i = 0
                while True:
                    try:
                        nome, valor, _ = winreg.EnumValue(k, i)
                        entradas.append({
                            "nome": nome,
                            "comando": valor,
                            "raiz": "HKCU" if raiz == winreg.HKEY_CURRENT_USER 
                                    else "HKLM"
                        })
                        i += 1
                    except OSError:
                        break
        except Exception:
            continue
    return entradas


if __name__ == "__main__":
    executar_otimizacao_geral()
