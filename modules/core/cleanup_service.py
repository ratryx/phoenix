import os
import shutil
import glob
from pathlib import Path

import stat

def bytes_to_mb(valor: int) -> float:
    return round(valor / (1024 ** 2), 2)

def is_safe_path(caminho: str, raiz_autorizada: str) -> bool:
    """Verifica se o caminho final esta dentro da raiz autorizada, sem symlinks escapando."""
    try:
        real_path = os.path.normcase(os.path.normpath(os.path.realpath(caminho)))
        real_root = os.path.normcase(os.path.normpath(os.path.realpath(raiz_autorizada)))
        return os.path.commonpath([real_path, real_root]) == real_root
    except ValueError:
        return False
    except Exception:
        return False

def _is_reparse_point(filepath: Path, st=None) -> bool:
    try:
        if st is None:
            st = os.lstat(str(filepath))
        return bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except AttributeError:
        return filepath.is_symlink() or filepath.is_junction()
    except Exception:
        return True


def _obter_alvos_limpeza(incluir_lixeira=False) -> dict:
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    
    alvos = {}
    
    if local_appdata:
        alvos["temp_usuario"] = {
            "nome": "Arquivos temporários do usuário",
            "caminho": os.path.join(local_appdata, "Temp"),
            "raiz_autorizada": os.path.join(local_appdata, "Temp"),
            "tipo": "diretorio"
        }
        
    alvos["temp_windows"] = {
        "nome": "Arquivos temporários do Windows",
        "caminho": r"C:\Windows\Temp",
        "raiz_autorizada": r"C:\Windows\Temp",
        "tipo": "diretorio"
    }
    
    if local_appdata:
        alvos["wer_archive"] = {
            "nome": "Relatórios de erro (Archive)",
            "caminho": os.path.join(local_appdata, "Microsoft", "Windows", "WER", "ReportArchive"),
            "raiz_autorizada": os.path.join(local_appdata, "Microsoft", "Windows", "WER", "ReportArchive"),
            "tipo": "diretorio"
        }
        alvos["wer_queue"] = {
            "nome": "Relatórios de erro (Queue)",
            "caminho": os.path.join(local_appdata, "Microsoft", "Windows", "WER", "ReportQueue"),
            "raiz_autorizada": os.path.join(local_appdata, "Microsoft", "Windows", "WER", "ReportQueue"),
            "tipo": "diretorio"
        }
        alvos["crash_dumps"] = {
            "nome": "Dumps de memória",
            "caminho": os.path.join(local_appdata, "CrashDumps"),
            "raiz_autorizada": os.path.join(local_appdata, "CrashDumps"),
            "tipo": "diretorio"
        }
        alvos["d3ds_cache"] = {
            "nome": "DirectX Shader Cache",
            "caminho": os.path.join(local_appdata, "D3DSCache"),
            "raiz_autorizada": os.path.join(local_appdata, "D3DSCache"),
            "tipo": "diretorio"
        }
        alvos["thumbcache"] = {
            "nome": "Cache de miniaturas",
            "caminho": os.path.join(local_appdata, "Microsoft", "Windows", "Explorer"),
            "raiz_autorizada": os.path.join(local_appdata, "Microsoft", "Windows", "Explorer"),
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
                    "raiz_autorizada": base_dir,
                    "tipo": "chromium_cache"
                }

        # Firefox
        firefox_dir = os.path.join(local_appdata, "Mozilla", "Firefox", "Profiles")
        if os.path.isdir(firefox_dir):
            alvos["cache_firefox"] = {
                "nome": "Cache do Firefox",
                "caminho": firefox_dir,
                "raiz_autorizada": firefox_dir,
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

def _remover_arquivo(filepath: Path, raiz_autorizada: str, cancel_event) -> dict:
    from modules.core.exceptions import JobCancelledError
    try:
        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()
            
        if not is_safe_path(str(filepath), raiz_autorizada):
            return {"removidos": 0, "ignorados": 1, "bytes": 0}
            
        st1 = os.lstat(str(filepath))
        if stat.S_ISLNK(st1.st_mode) or _is_reparse_point(filepath, st1):
            return {"removidos": 0, "ignorados": 1, "bytes": 0}
            
        tamanho = st1.st_size
        
        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()
            
        st2 = os.lstat(str(filepath))
        if (st1.st_ino != st2.st_ino or 
            st1.st_dev != st2.st_dev or 
            st1.st_size != st2.st_size or 
            st1.st_mode != st2.st_mode):
            return {"removidos": 0, "ignorados": 1, "bytes": 0}
            
        if stat.S_ISLNK(st2.st_mode) or _is_reparse_point(filepath, st2):
            return {"removidos": 0, "ignorados": 1, "bytes": 0}
            
        if not is_safe_path(str(filepath), raiz_autorizada):
            return {"removidos": 0, "ignorados": 1, "bytes": 0}
            
        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()
            
        filepath.unlink()
        return {"removidos": 1, "ignorados": 0, "bytes": tamanho}
    except JobCancelledError:
        raise
    except Exception:
        return {"removidos": 0, "ignorados": 1, "bytes": 0}

def _remover_diretorio_recursivo(dirpath: Path, raiz_autorizada: str, cancel_event) -> dict:
    from modules.core.exceptions import JobCancelledError
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()
        
    total = {"removidos": 0, "ignorados": 0, "bytes": 0, "erros": []}
    
    try:
        if not dirpath.exists() or dirpath.is_symlink() or dirpath.is_junction() or _is_reparse_point(dirpath):
            return total
            
        if not is_safe_path(str(dirpath), raiz_autorizada):
            return total
            
        for item in dirpath.iterdir():
            if cancel_event and cancel_event.is_set():
                raise JobCancelledError()
                
            try:
                if not is_safe_path(str(item), raiz_autorizada):
                    total["ignorados"] += 1
                    total["erros"].append(f"Caminho inseguro: {item}")
                    continue
                    
                if item.is_junction() or item.is_symlink() or _is_reparse_point(item):
                    total["ignorados"] += 1
                    total["erros"].append(f"Link ou reparse point ignorado: {item}")
                    continue
                    
                if item.is_file():
                    res = _remover_arquivo(item, raiz_autorizada, cancel_event)
                    total["removidos"] += res["removidos"]
                    total["ignorados"] += res["ignorados"]
                    total["bytes"] += res["bytes"]
                    if res["ignorados"] > 0:
                        total["erros"].append(f"Não removido: {item}")
                elif item.is_dir():
                    res = _remover_diretorio_recursivo(item, raiz_autorizada, cancel_event)
                    total["removidos"] += res.get("removidos", 0)
                    total["ignorados"] += res.get("ignorados", 0)
                    total["bytes"] += res.get("bytes", 0)
                    total["erros"].extend(res.get("erros", []))
                    
                    try:
                        if is_safe_path(str(item), raiz_autorizada):
                            item.rmdir()
                    except Exception:
                        pass
            except JobCancelledError:
                raise
            except Exception as e:
                total["ignorados"] += 1
                total["erros"].append(f"Erro em {item}: {str(e)}")
    except JobCancelledError:
        raise
    except Exception as e:
        total["ignorados"] += 1
        total["erros"].append(f"Falha de acesso em {dirpath}: {str(e)}")
            
    return total

def _processar_alvo(alvo_id, info, cancel_event) -> dict:
    from modules.core.exceptions import JobCancelledError
    
    total = {"removidos": 0, "ignorados": 0, "bytes": 0, "erros": []}
    
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()
        
    tipo = info["tipo"]
    
    if tipo == "lixeira":
        return _limpar_lixeira(cancel_event)
        
    if "caminho" not in info or not os.path.exists(info["caminho"]):
        return total
        
    caminho_base = info["caminho"]
    
    if "raiz_autorizada" not in info:
        return total
        
    raiz_autorizada = info["raiz_autorizada"]
    
    if tipo == "diretorio":
        res = _remover_diretorio_recursivo(Path(caminho_base), raiz_autorizada, cancel_event)
        total["removidos"] += res.get("removidos", 0)
        total["ignorados"] += res.get("ignorados", 0)
        total["bytes"] += res.get("bytes", 0)
        total["erros"].extend(res.get("erros", []))
        
    elif tipo == "glob":
        if "raiz_autorizada" not in info or not is_safe_path(caminho_base, info["raiz_autorizada"]):
            return total
            
        try:
            for filepath in Path(caminho_base).glob(info["padrao"]):
                if cancel_event and cancel_event.is_set():
                    raise JobCancelledError()
                    
                if filepath.is_file() and not filepath.is_symlink() and not filepath.is_junction() and not _is_reparse_point(filepath):
                    res = _remover_arquivo(filepath, info["raiz_autorizada"], cancel_event)
                    total["removidos"] += res["removidos"]
                    total["ignorados"] += res["ignorados"]
                    total["bytes"] += res["bytes"]
                    if res["ignorados"] > 0:
                        total["erros"].append(f"Não removido: {filepath}")
        except JobCancelledError:
            raise
        except Exception as e:
            total["ignorados"] += 1
            total["erros"].append(f"Erro no glob: {str(e)}")
                
    elif tipo == "chromium_cache":
        try:
            for perfil in Path(caminho_base).iterdir():
                if not perfil.is_dir() or perfil.is_symlink() or perfil.is_junction():
                    continue
                subpastas = ["Cache", "Code Cache", "GPUCache", "GrShaderCache", "DawnCache"]
                for sub in subpastas:
                    sub_path = perfil / sub
                    if sub_path.exists() and sub_path.is_dir() and not sub_path.is_symlink() and not sub_path.is_junction():
                        res = _remover_diretorio_recursivo(sub_path, raiz_autorizada, cancel_event)
                        total["removidos"] += res.get("removidos", 0)
                        total["ignorados"] += res.get("ignorados", 0)
                        total["bytes"] += res.get("bytes", 0)
                        total["erros"].extend(res.get("erros", []))
        except Exception as e:
            total["ignorados"] += 1
            total["erros"].append(f"Erro na iteração Chromium: {str(e)}")
                        
    elif tipo == "firefox_cache":
        try:
            for perfil in Path(caminho_base).iterdir():
                if not perfil.is_dir() or perfil.is_symlink() or perfil.is_junction():
                    continue
                sub_path = perfil / "cache2"
                if sub_path.exists() and sub_path.is_dir() and not sub_path.is_symlink() and not sub_path.is_junction():
                    res = _remover_diretorio_recursivo(sub_path, raiz_autorizada, cancel_event)
                    total["removidos"] += res.get("removidos", 0)
                    total["ignorados"] += res.get("ignorados", 0)
                    total["bytes"] += res.get("bytes", 0)
                    total["erros"].extend(res.get("erros", []))
        except Exception as e:
            total["ignorados"] += 1
            total["erros"].append(f"Erro na iteração Firefox: {str(e)}")

    return total


def executar_limpeza(progress_callback=None, cancel_event=None, incluir_lixeira=False, injetar_alvos=None) -> dict:
    """Executa a limpeza de cache e lixo do sistema de forma segura e não visual."""
    from modules.core.exceptions import JobCancelledError
    
    if injetar_alvos is not None:
        for k, v in injetar_alvos.items():
            if v.get("tipo") != "lixeira" and "raiz_autorizada" not in v:
                raise ValueError(f"Alvo injetado '{k}' sem raiz_autorizada")
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
            cat_result["arquivos_removidos"] = stats.get("removidos", 0)
            cat_result["arquivos_ignorados"] = stats.get("ignorados", 0)
            cat_result["espaco_liberado_bytes"] = stats.get("bytes", 0)
            
            resultado["arquivos_removidos"] += stats.get("removidos", 0)
            resultado["arquivos_ignorados"] += stats.get("ignorados", 0)
            resultado["espaco_liberado_bytes"] += stats.get("bytes", 0)
            
            if stats.get("ignorados", 0) > 0:
                cat_result["status"] = "parcial"
                resultado["parcial"] = True
                erros = stats.get("erros", [])
                if erros:
                    resultado["avisos"].append(f"Erros em {info['nome']}: {'; '.join(erros[:5])}")
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
