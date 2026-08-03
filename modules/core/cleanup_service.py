import os
import shutil
import glob
from pathlib import Path

def bytes_to_mb(valor: int) -> float:
    return round(valor / (1024 ** 2), 2)

def is_safe_path(caminho: str, raiz_autorizada: str) -> bool:
    """Verifica se o caminho final esta dentro da raiz autorizada, sem symlinks escapando."""
    try:
        real_path = os.path.realpath(caminho)
        real_root = os.path.realpath(raiz_autorizada)
        return real_path.startswith(real_root)
    except Exception:
        return False

def _obter_alvos_limpeza(incluir_lixeira=False) -> dict:
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    temp_dir = os.environ.get("TEMP", "")
    
    alvos = {}
    
    if temp_dir:
        alvos["temp_usuario"] = {
            "nome": "Arquivos temporários do usuário",
            "caminho": temp_dir,
            "tipo": "diretorio"
        }
        
    alvos["temp_windows"] = {
        "nome": "Arquivos temporários do Windows",
        "caminho": r"C:\Windows\Temp",
        "tipo": "diretorio"
    }
    
    if local_appdata:
        alvos["wer_archive"] = {
            "nome": "Relatórios de erro (Archive)",
            "caminho": os.path.join(local_appdata, "Microsoft", "Windows", "WER", "ReportArchive"),
            "tipo": "diretorio"
        }
        alvos["wer_queue"] = {
            "nome": "Relatórios de erro (Queue)",
            "caminho": os.path.join(local_appdata, "Microsoft", "Windows", "WER", "ReportQueue"),
            "tipo": "diretorio"
        }
        alvos["crash_dumps"] = {
            "nome": "Dumps de memória",
            "caminho": os.path.join(local_appdata, "CrashDumps"),
            "tipo": "diretorio"
        }
        alvos["d3ds_cache"] = {
            "nome": "DirectX Shader Cache",
            "caminho": os.path.join(local_appdata, "D3DSCache"),
            "tipo": "diretorio"
        }
        alvos["thumbcache"] = {
            "nome": "Cache de miniaturas",
            "caminho": os.path.join(local_appdata, "Microsoft", "Windows", "Explorer"),
            "tipo": "glob",
            "padrao": "thumbcache_*.db"
        }
        
        # Chrome, Edge, Brave (Chromium based)
        for browser, path_part in [
            ("Chrome", r"Google\Chrome\User Data"),
            ("Edge", r"Microsoft\Edge\User Data"),
            ("Brave", r"BraveSoftware\Brave-Browser\User Data")
        ]:
            base_dir = os.path.join(local_appdata, path_part)
            if os.path.isdir(base_dir):
                alvos[f"cache_{browser.lower()}"] = {
                    "nome": f"Cache do {browser}",
                    "caminho": base_dir,
                    "tipo": "chromium_cache"
                }

        # Firefox
        firefox_dir = os.path.join(local_appdata, "Mozilla", "Firefox", "Profiles")
        if os.path.isdir(firefox_dir):
            alvos["cache_firefox"] = {
                "nome": "Cache do Firefox",
                "caminho": firefox_dir,
                "tipo": "firefox_cache"
            }
            
    # Lixeira
    if incluir_lixeira:
        alvos["lixeira"] = {
            "nome": "Lixeira",
            "tipo": "lixeira"
        }

    return alvos

def _limpar_lixeira(cancel_event) -> dict:
    # A lixeira é limpa via PowerShell
    if cancel_event and cancel_event.is_set():
        from modules.core.exceptions import JobCancelledError
        raise JobCancelledError()
        
    from modules.core.windows_command import run_windows_command
    res = run_windows_command(
        ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
        operation_name="Limpar Lixeira",
        timeout_seconds=30.0
    )
    if res.ok:
        return {"removidos": 1, "ignorados": 0, "bytes": 0}
    return {"removidos": 0, "ignorados": 1, "bytes": 0}

def _remover_arquivo(filepath: Path) -> dict:
    try:
        if filepath.is_symlink():
            filepath.unlink()
            return {"removidos": 1, "ignorados": 0, "bytes": 0}
            
        tamanho = filepath.stat().st_size
        filepath.unlink()
        return {"removidos": 1, "ignorados": 0, "bytes": tamanho}
    except Exception:
        return {"removidos": 0, "ignorados": 1, "bytes": 0}

def _remover_diretorio_recursivo(dirpath: Path, raiz_autorizada: str, cancel_event) -> dict:
    if cancel_event and cancel_event.is_set():
        from modules.core.exceptions import JobCancelledError
        raise JobCancelledError()
        
    total = {"removidos": 0, "ignorados": 0, "bytes": 0}
    
    if not dirpath.exists() or dirpath.is_symlink() or dirpath.is_junction():
        return total
        
    for item in dirpath.iterdir():
        if cancel_event and cancel_event.is_set():
            from modules.core.exceptions import JobCancelledError
            raise JobCancelledError()
            
        try:
            if item.is_junction() or item.is_symlink():
                continue
                
            if item.is_file():
                res = _remover_arquivo(item)
                total["removidos"] += res["removidos"]
                total["ignorados"] += res["ignorados"]
                total["bytes"] += res["bytes"]
            elif item.is_dir():
                res = _remover_diretorio_recursivo(item, raiz_autorizada, cancel_event)
                total["removidos"] += res["removidos"]
                total["ignorados"] += res["ignorados"]
                total["bytes"] += res["bytes"]
                
                try:
                    item.rmdir()
                except Exception:
                    pass
        except Exception:
            total["ignorados"] += 1
            
    return total

def _processar_alvo(alvo_id, info, cancel_event) -> dict:
    from modules.core.exceptions import JobCancelledError
    
    total = {"removidos": 0, "ignorados": 0, "bytes": 0}
    
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()
        
    tipo = info["tipo"]
    
    if tipo == "lixeira":
        return _limpar_lixeira(cancel_event)
        
    if "caminho" not in info or not os.path.exists(info["caminho"]):
        return total
        
    caminho_base = info["caminho"]
    
    if tipo == "diretorio":
        res = _remover_diretorio_recursivo(Path(caminho_base), caminho_base, cancel_event)
        total["removidos"] += res["removidos"]
        total["ignorados"] += res["ignorados"]
        total["bytes"] += res["bytes"]
        
    elif tipo == "glob":
        for filepath in Path(caminho_base).glob(info["padrao"]):
            if cancel_event and cancel_event.is_set():
                raise JobCancelledError()
            if filepath.is_file() and not filepath.is_symlink():
                res = _remover_arquivo(filepath)
                total["removidos"] += res["removidos"]
                total["ignorados"] += res["ignorados"]
                total["bytes"] += res["bytes"]
                
    elif tipo == "chromium_cache":
        for perfil in Path(caminho_base).iterdir():
            if not perfil.is_dir() or perfil.is_symlink() or perfil.is_junction():
                continue
            subpastas = ["Cache", "Code Cache", "GPUCache", "GrShaderCache", "DawnCache"]
            for sub in subpastas:
                sub_path = perfil / sub
                if sub_path.exists() and sub_path.is_dir() and not sub_path.is_symlink() and not sub_path.is_junction():
                    res = _remover_diretorio_recursivo(sub_path, str(sub_path), cancel_event)
                    total["removidos"] += res["removidos"]
                    total["ignorados"] += res["ignorados"]
                    total["bytes"] += res["bytes"]
                    
    elif tipo == "firefox_cache":
        for perfil in Path(caminho_base).iterdir():
            if not perfil.is_dir() or perfil.is_symlink() or perfil.is_junction():
                continue
            sub_path = perfil / "cache2"
            if sub_path.exists() and sub_path.is_dir() and not sub_path.is_symlink() and not sub_path.is_junction():
                res = _remover_diretorio_recursivo(sub_path, str(sub_path), cancel_event)
                total["removidos"] += res["removidos"]
                total["ignorados"] += res["ignorados"]
                total["bytes"] += res["bytes"]

    return total


def executar_limpeza(progress_callback=None, cancel_event=None, incluir_lixeira=False, injetar_alvos=None) -> dict:
    """Executa a limpeza de cache e lixo do sistema de forma segura e não visual."""
    from modules.core.exceptions import JobCancelledError
    
    if injetar_alvos is not None:
        alvos = injetar_alvos
    else:
        alvos = _obter_alvos_limpeza(incluir_lixeira=incluir_lixeira)
        
    resultado = {
        "ok": True,
        "parcial": False,
        "espaco_liberado_bytes": 0,
        "espaco_liberado_mb": 0.0,
        "arquivos_removidos": 0,
        "arquivos_ignorados": 0,
        "categorias": [],
        "avisos": []
    }
    
    total_categorias = len(alvos)
    
    for i, (cat_id, info) in enumerate(alvos.items()):
        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()
            
        cat_result = {
            "id": cat_id,
            "nome": info["nome"],
            "status": "analisando",
            "percentual": 0,
            "arquivos_removidos": 0,
            "arquivos_ignorados": 0,
            "espaco_liberado_bytes": 0
        }
        resultado["categorias"].append(cat_result)
        
        if progress_callback:
            progress_callback(
                mensagem=f"Limpando: {info['nome']}",
                progresso=int((i / total_categorias) * 100) if total_categorias else 100,
                detalhes={
                    "categoria": info["nome"],
                    "categoria_percentual": 0,
                    "arquivos_processados": resultado["arquivos_removidos"],
                    "espaco_liberado_mb": bytes_to_mb(resultado["espaco_liberado_bytes"])
                }
            )
            
        cat_result["status"] = "limpando"
        
        try:
            stats = _processar_alvo(cat_id, info, cancel_event)
            cat_result["arquivos_removidos"] = stats["removidos"]
            cat_result["arquivos_ignorados"] = stats["ignorados"]
            cat_result["espaco_liberado_bytes"] = stats["bytes"]
            
            resultado["arquivos_removidos"] += stats["removidos"]
            resultado["arquivos_ignorados"] += stats["ignorados"]
            resultado["espaco_liberado_bytes"] += stats["bytes"]
            
            if stats["ignorados"] > 0:
                cat_result["status"] = "parcial"
                resultado["parcial"] = True
            else:
                cat_result["status"] = "concluido"
                
        except JobCancelledError:
            cat_result["status"] = "cancelado"
            resultado["ok"] = False
            resultado["avisos"].append(f"Cancelado durante: {info['nome']}")
            raise
        except Exception as e:
            cat_result["status"] = "falhou"
            resultado["ok"] = False
            resultado["parcial"] = True
            resultado["avisos"].append(f"Falha em {info['nome']}: {str(e)}")
            
        cat_result["percentual"] = 100
        
    resultado["espaco_liberado_mb"] = bytes_to_mb(resultado["espaco_liberado_bytes"])
    
    if progress_callback:
        progress_callback(
            mensagem="Concluído",
            progresso=100,
            detalhes={
                "categoria": "Finalizado",
                "categoria_percentual": 100,
                "arquivos_processados": resultado["arquivos_removidos"],
                "espaco_liberado_mb": resultado["espaco_liberado_mb"]
            }
        )
        
    return resultado
