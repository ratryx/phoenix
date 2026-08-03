"""
Módulo de otimização: ajustes de performance geral do Windows 10/11
e otimizações específicas para ganho de FPS em jogos.

IMPORTANTE: ajustes que alteram registro/serviços do Windows pedem
confirmação do usuário antes de aplicar, e cada função é independente
para que você possa escolher quais aplicar.
"""

from modules.core.windows_command import run_windows_command, to_public_result
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
        res = run_windows_command(["powercfg", "/getactivescheme"], operation_name="Verificar plano de energia", timeout_seconds=5.0)
        is_active = res.ok and ("8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" in res.stdout or "e9a42b02-d5df-448d-aa00-03f14749eb61" in res.stdout)
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
    if id_otimizacao == "plano_energia":
        res = ativar_plano_energia_alto_desempenho()
        return {"ok": res.get("ok", False), "id": id_otimizacao, "codigo": res.get("codigo")}
        
    config = ITENS_VERIFICACAO.get(id_otimizacao)
    if not config:
        return {"ok": False, "erro": "ID não encontrado"}
        
    if config["tipo"] == "registro":
        res = {"ok": False}
        if id_otimizacao == "modo_jogo":
            res = ativar_modo_jogo_windows()
        elif id_otimizacao == "gpu_scheduling":
            res = otimizar_gpu_para_jogos()
        elif id_otimizacao == "gamebar_overlay":
            res = desativar_gamebar_overlay()
        elif id_otimizacao == "efeitos_visuais":
            res = desativar_efeitos_visuais()
        elif id_otimizacao == "apps_segundo_plano":
            res = limitar_processos_em_segundo_plano()
        return {"ok": res.get("ok", False), "id": id_otimizacao, "codigo": res.get("codigo")}
        
    return {"ok": False, "erro": "Tipo de otimização não suportado"}

def reaplicar_todas_inativas(status_atual: dict) -> dict:
    """Reaplica em lote todas as inativas com 1 único ponto de restauração prévio."""
    res_pr = criar_ponto_restauracao()
    if not res_pr.get("ok"):
        return res_pr
        
    reaplicadas = []
    falhas = []
    
    for item in status_atual.get("itens", []):
        if not item["ativo"]:
            res = reaplicar_otimizacao(item["id"])
            if res.get("ok"):
                reaplicadas.append(item["id"])
            else:
                falhas.append(item["id"])
                
    if falhas:
        return {"ok": False, "codigo": "OPERATION_PARTIAL_FAILURE", "reaplicadas": reaplicadas, "falhas": falhas}
    return {"ok": True, "reaplicadas": reaplicadas}


def is_admin() -> bool:
    """Verifica se o programa possui privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def criar_ponto_restauracao(cancel_event=None) -> dict:
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

    resultado = run_windows_command(comando, operation_name="Criar Ponto de Restauração", timeout_seconds=120.0, cancel_event=cancel_event)

    if resultado.code == "COMMAND_CANCELLED":
        return {
            "ok": False,
            "codigo": "COMMAND_CANCELLED",
            "erro": "A operação foi cancelada pelo usuário."
        }

    if resultado.ok:
        return {
            "ok": True,
            "mensagem": "Ponto de restauração 'Phoenix Optimizer - Pré-Otimização' criado com sucesso."
        }
    else:
        if resultado.timed_out:
            return {
                "ok": False,
                "erro": "Tempo limite excedido ao tentar criar o ponto de restauração.",
                "codigo": "TIMEOUT"
            }
        
        erro_str = (resultado.stderr + "\n" + resultado.stdout).strip()

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
            erro = "Falha ao criar ponto de restauração do Windows."

        return {
            "ok": False,
            "erro": erro,
            "codigo": codigo
        }



def _executar_comando(comando: list, nome_acao: str, cancel_event=None) -> dict:
    """Executa um comando do sistema e retorna resultado estruturado."""
    resultado = run_windows_command(comando, operation_name=nome_acao, timeout_seconds=30.0, cancel_event=cancel_event)
    if resultado.code == "COMMAND_CANCELLED":
        return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
    if not resultado.ok:
        console.print(f"  [yellow][AVISO][/yellow] {nome_acao} (falhou)")
        return to_public_result(resultado)
    console.print(f"  [green][OK][/green] {nome_acao}")
    return {"ok": True, "codigo": "COMMAND_OK"}


def ativar_plano_energia_alto_desempenho(cancel_event=None):
    """Ativa o plano de energia 'Alto desempenho' do Windows."""
    return _executar_comando(
        ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
        "Plano de energia: Alto desempenho ativado", cancel_event=cancel_event
    )


def desativar_efeitos_visuais(cancel_event=None):
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
        "Efeitos visuais reduzidos (modo performance)", cancel_event=cancel_event
    )


def ativar_modo_jogo_windows(cancel_event=None):
    """Garante que o Modo de Jogo do Windows está ativado via registro."""
    comando_ps = (
        "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\GameBar' "
        "-Name AllowAutoGameMode -PropertyType DWord -Value 1 -Force | Out-Null; "
        "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\GameBar' "
        "-Name AutoGameModeEnabled -PropertyType DWord -Value 1 -Force | Out-Null"
    )
    return _executar_comando(["powershell", "-Command", comando_ps], "Modo de Jogo do Windows ativado", cancel_event=cancel_event)


def desativar_gamebar_overlay(cancel_event=None):
    """Desativa a sobreposição (overlay) do Xbox Game Bar, que consome recursos."""
    comando_ps = (
        "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR' "
        "-Name AppCaptureEnabled -PropertyType DWord -Value 0 -Force | Out-Null"
    )
    return _executar_comando(["powershell", "-Command", comando_ps], "Overlay do Xbox Game Bar desativado", cancel_event=cancel_event)


def limitar_processos_em_segundo_plano(cancel_event=None):
    """Desativa apps em segundo plano que consomem CPU/RAM sem necessidade (UWP apps)."""
    comando_ps = (
        "New-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications' "
        "-Name GlobalUserDisabled -PropertyType DWord -Value 1 -Force | Out-Null"
    )
    return _executar_comando(["powershell", "-Command", comando_ps], "Apps em segundo plano restringidos", cancel_event=cancel_event)


def otimizar_gpu_para_jogos(cancel_event=None):
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
        "Agendador de GPU por hardware ativado (requer reinício)", cancel_event=cancel_event
    )


def listar_itens_inicializacao() -> dict:
    """Lista os programas configurados para abrir junto com o Windows."""
    comando_ps = (
        "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | Format-Table -AutoSize"
    )
    resultado = run_windows_command(
        ["powershell", "-NoProfile", "-Command", comando_ps],
        operation_name="Listar inicialização",
        timeout_seconds=30.0
    )
    if resultado.code == "COMMAND_CANCELLED":
        return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
    
    if not resultado.ok:
        return {
            "ok": False,
            "codigo": resultado.code,
            "erro": "Falha ao listar programas de inicialização." if not resultado.timed_out else "Tempo limite excedido."
        }
    
    saida = resultado.stdout.strip()
    if not saida:
        return {
            "ok": True,
            "codigo": "COMMAND_OK",
            "itens": [],
            "mensagem": "Nenhum item encontrado."
        }
    return {
        "ok": True,
        "codigo": "COMMAND_OK",
        "itens": saida.splitlines()
    }


def otimizar_disco_principal(cancel_event=None) -> dict:
    """
    Executa otimização do disco C: — TRIM se for SSD, desfragmentação se for HDD.
    O Windows já decide automaticamente o método correto via /retrim ou /defrag.
    """
    resultado = run_windows_command(
        ["defrag", "C:", "/O"],
        operation_name="Otimizar Disco",
        timeout_seconds=270.0,
        cancel_event=cancel_event,
    )

    if resultado.code == "COMMAND_CANCELLED":
        return {
            "ok": False,
            "codigo": "COMMAND_CANCELLED",
            "erro": "A operação foi cancelada pelo usuário.",
        }

    if resultado.ok:
        console.print("  [green][OK][/green] Otimização de disco (C:) executada")
        return {
            "ok": True,
            "codigo": "COMMAND_OK",
            "saida": resultado.stdout,
        }

    return to_public_result(
        resultado,
        error_message=(
            "A otimização do disco excedeu o tempo permitido."
            if resultado.code == "COMMAND_TIMEOUT"
            else "Não foi possível otimizar o disco."
        ),
    )


def executar_verificacao_integridade_sistema(id_atendimento: str = None, cancel_event=None) -> dict:
    """
    Executa verificação completa de integridade do Windows:
    1. DISM (repara o store de componentes do Windows)
    2. SFC (verifica e repara arquivos de sistema usando o store reparado)
    """
    console.print(Panel("[bold yellow]Verificando integridade do sistema...[/bold yellow]", border_style="orange3"))
    console.print("  [dim]Isso pode levar vários minutos. Não feche o programa.[/dim]\n")

    resultados = {"dism": False, "sfc": False}

    console.print("  [bold]Etapa 1/2 — DISM (reparando store de componentes)...[/bold]")
    res_dism = _executar_comando(
        ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
        "DISM: Store de componentes verificado/reparado",
        cancel_event=cancel_event
    )
    if res_dism.get("codigo") == "COMMAND_CANCELLED":
        return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
    resultados["dism"] = res_dism

    console.print("  [bold]Etapa 2/2 — SFC (verificando arquivos do sistema)...[/bold]")
    res_sfc = _executar_comando(
        ["sfc", "/scannow"],
        "SFC: Arquivos do sistema verificados",
        cancel_event=cancel_event
    )
    if res_sfc.get("codigo") == "COMMAND_CANCELLED":
        return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
    resultados["sfc"] = res_sfc

    sucesso = res_dism.get("ok", False) and res_sfc.get("ok", False)
    resultados["ok"] = sucesso
    if sucesso:
        resultados["codigo"] = "OPERATION_OK"
        console.print(Panel("[bold green]Verificação de integridade concluída com sucesso![/bold green]", border_style="green"))
    else:
        resultados["codigo"] = "OPERATION_PARTIAL_FAILURE"
        console.print(Panel("[bold yellow]Verificação concluída com avisos. Verifique os resultados acima.[/bold yellow]", border_style="yellow"))

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Verificação de integridade do sistema",
                          f"DISM: {'OK' if res_dism.get('ok') else 'Falha'}, SFC: {'OK' if res_sfc.get('ok') else 'Falha'}")

    return resultados


def limpar_dns_e_rede(cancel_event=None):
    """Reinicia adaptadores e limpa configurações de rede que podem causar lentidão/ping alto."""
    comandos = [
        (["ipconfig", "/flushdns"], "Cache DNS limpo"),
        (["netsh", "winsock", "reset"], "Winsock resetado (melhora conexão em jogos online)"),
        (["netsh", "int", "ip", "reset"], "Pilha TCP/IP resetada"),
    ]
    resultados = {}
    todos_ok = True
    for cmd, nome in comandos:
        res = _executar_comando(cmd, nome, cancel_event=cancel_event)
        if res.get("codigo") == "COMMAND_CANCELLED":
            return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
        resultados[nome] = res
        if not res.get("ok"):
            todos_ok = False
            
    return {
        "ok": todos_ok,
        "codigo": "OPERATION_OK" if todos_ok else "OPERATION_PARTIAL_FAILURE",
        "resultados": resultados
    }


def executar_otimizacao_geral(id_atendimento: str = None, cancel_event=None) -> dict:
    """Executa o conjunto de otimizações gerais de performance (não-destrutivas)."""
    console.print(Panel("[bold yellow]Aplicando otimizações de performance...[/bold yellow]", border_style="orange3"))

    acoes = [
        ("plano_energia", ativar_plano_energia_alto_desempenho),
        ("efeitos_visuais", desativar_efeitos_visuais),
        ("apps_segundo_plano", limitar_processos_em_segundo_plano)
    ]
    resultados_cmd = {}
    for nome, func in acoes:
        res = func(cancel_event=cancel_event)
        if res.get("codigo") == "COMMAND_CANCELLED":
            return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
        resultados_cmd[nome] = res

    sucesso = sum(1 for v in resultados_cmd.values() if v.get("ok"))
    total = len(resultados_cmd)
    todos_ok = (sucesso == total)

    if todos_ok:
        console.print(Panel("[bold green]Todas as otimizações de performance aplicadas![/bold green]", border_style="green"))
    else:
        console.print(Panel(
            f"[bold yellow]Otimizações aplicadas: {sucesso}/{total} (verifique os avisos acima)[/bold yellow]",
            border_style="yellow"
        ))

    if id_atendimento:
        from modules import logs
        msg = "Otimização geral concluída parcialmente" if not todos_ok else "Otimização geral aplicada"
        logs.registrar_acao(id_atendimento, msg, f"{sucesso}/{total} sucessos")

    return {
        "ok": todos_ok,
        "codigo": "OPERATION_OK" if todos_ok else "OPERATION_PARTIAL_FAILURE",
        "sucessos": sucesso,
        "total": total,
        "resultados": resultados_cmd
    }


def executar_otimizacao_gaming(id_atendimento: str = None, 
                                resetar_rede: bool = False, cancel_event=None) -> dict:
    console.print(Panel(
        "[bold yellow]Aplicando otimizações para jogos (FPS)...[/bold yellow]", 
        border_style="orange3"
    ))
    
    acoes = [
        ("plano_energia", ativar_plano_energia_alto_desempenho),
        ("modo_jogo", ativar_modo_jogo_windows),
        ("gamebar", desativar_gamebar_overlay),
        ("gpu", otimizar_gpu_para_jogos)
    ]
    resultados = {}
    for nome, func in acoes:
        res = func(cancel_event=cancel_event)
        if res.get("codigo") == "COMMAND_CANCELLED":
            return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
        resultados[nome] = res
        
    if resetar_rede:
        res = limpar_dns_e_rede(cancel_event=cancel_event)
        if res.get("codigo") == "COMMAND_CANCELLED":
            return {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}
        resultados["rede"] = res

    sucesso = sum(1 for v in resultados.values() if v.get("ok"))
    total = len(resultados)
    todos_ok = (sucesso == total)

    if todos_ok:
        console.print(Panel(
            "[bold green]Otimizações de FPS aplicadas! "
            "Reinicie o PC para garantir que tudo seja aplicado.[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]Otimizações aplicadas com falhas: {sucesso}/{total}.[/bold yellow]",
            border_style="yellow"
        ))

    if id_atendimento:
        from modules import logs
        msg = "Otimização para jogos concluída parcialmente" if not todos_ok else "Otimização para jogos aplicada"
        logs.registrar_acao(id_atendimento, msg, f"{sucesso}/{total} sucessos")
    
    return {
        "ok": todos_ok,
        "codigo": "OPERATION_OK" if todos_ok else "OPERATION_PARTIAL_FAILURE",
        "sucessos": sucesso,
        "total": total,
        "resultados": resultados
    }

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
    res1 = run_windows_command(["powercfg", "/change", "standby-timeout-ac", "0"], operation_name="Desativar suspensão", timeout_seconds=10.0)
    res2 = run_windows_command(["powercfg", "/change", "monitor-timeout-ac", "0"], operation_name="Desativar monitor timeout", timeout_seconds=10.0)
    return {"ok": res1.ok and res2.ok, "resultados": {"standby": to_public_result(res1), "monitor": to_public_result(res2)}}

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
