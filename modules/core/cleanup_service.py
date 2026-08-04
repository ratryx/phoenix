import os
import shutil
from pathlib import Path
import stat

def bytes_to_mb(valor: int) -> float:
    return round(valor / (1024 ** 2), 2)

def is_safe_path(caminho: str, raiz_autorizada: str) -> bool:
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

def _enumerar_seguro(caminho: str, raiz_autorizada: str, cancel_event, is_root=True):
    from modules.core.exceptions import JobCancelledError
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()
    
    try:
        it = os.scandir(caminho)
    except OSError:
        if is_root:
            raise
        return
        
    with it:
        for entry in it:
            if cancel_event and cancel_event.is_set():
                raise JobCancelledError()
            try:
                p = Path(entry.path)
                st = entry.stat(follow_symlinks=False)
                if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) or _is_reparse_point(p, st):
                    continue
                if not is_safe_path(entry.path, raiz_autorizada):
                    continue
                    
                yield entry.path, entry.is_dir(follow_symlinks=False)
                
                if entry.is_dir(follow_symlinks=False):
                    yield from _enumerar_seguro(entry.path, raiz_autorizada, cancel_event, is_root=False)
            except OSError:
                continue

def _obter_alvos_limpeza(incluir_lixeira=False) -> dict:
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    alvos = {}

    if local_appdata:
        temp_user = os.path.join(local_appdata, "Temp")
        alvos["temp_usuario"] = {
            "nome": "Arquivos temporários do usuário",
            "caminho": temp_user,
            "raiz_autorizada": temp_user,
            "tipo": "diretorio"
        }

    alvos["temp_windows"] = {
        "nome": "Arquivos temporários do Windows",
        "caminho": r"C:\Windows\Temp",
        "raiz_autorizada": r"C:\Windows\Temp",
        "tipo": "diretorio"
    }

    if local_appdata:
        wer_archive = os.path.join(local_appdata, "Microsoft", "Windows", "WER", "ReportArchive")
        alvos["wer_archive"] = {
            "nome": "Relatórios de erro (Archive)",
            "caminho": wer_archive,
            "raiz_autorizada": wer_archive,
            "tipo": "diretorio"
        }

        wer_queue = os.path.join(local_appdata, "Microsoft", "Windows", "WER", "ReportQueue")
        alvos["wer_queue"] = {
            "nome": "Relatórios de erro (Queue)",
            "caminho": wer_queue,
            "raiz_autorizada": wer_queue,
            "tipo": "diretorio"
        }

        crash_dumps = os.path.join(local_appdata, "CrashDumps")
        alvos["crash_dumps"] = {
            "nome": "Dumps de memória",
            "caminho": crash_dumps,
            "raiz_autorizada": crash_dumps,
            "tipo": "diretorio"
        }

        d3ds_cache = os.path.join(local_appdata, "D3DSCache")
        alvos["d3ds_cache"] = {
            "nome": "DirectX Shader Cache",
            "caminho": d3ds_cache,
            "raiz_autorizada": d3ds_cache,
            "tipo": "diretorio"
        }

        explorer = os.path.join(local_appdata, "Microsoft", "Windows", "Explorer")
        alvos["thumbcache"] = {
            "nome": "Cache de miniaturas",
            "caminho": explorer,
            "raiz_autorizada": explorer,
            "tipo": "glob",
            "padrao": "thumbcache_*.db"
        }

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

        firefox_dir = os.path.join(local_appdata, "Mozilla", "Firefox", "Profiles")
        if os.path.isdir(firefox_dir):
            alvos["cache_firefox"] = {
                "nome": "Cache do Firefox",
                "caminho": firefox_dir,
                "raiz_autorizada": firefox_dir,
                "tipo": "firefox_cache"
            }

    if incluir_lixeira:
        alvos["lixeira"] = {
            "tipo": "lixeira",
            "nome": "Lixeira do Sistema"
        }

    return alvos

def _contar_alvo(info, cancel_event) -> int:
    from modules.core.exceptions import JobCancelledError
    tipo = info.get("tipo")
    if tipo == "lixeira": return 1
    caminho = info.get("caminho")
    if not caminho or not os.path.exists(caminho): return 0
    raiz_autorizada = info.get("raiz_autorizada")
    if not raiz_autorizada: return 0
    
    count = 0
    if tipo == "diretorio":
        try:
            for path, is_dir in _enumerar_seguro(caminho, raiz_autorizada, cancel_event):
                count += 1
        except OSError:
            pass
    elif tipo == "glob":
        if is_safe_path(caminho, raiz_autorizada):
            try:
                for filepath in Path(caminho).glob(info["padrao"]):
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    if is_safe_path(str(filepath), raiz_autorizada):
                        count += 1
            except Exception:
                pass
    elif tipo in ("chromium_cache", "firefox_cache"):
        try:
            for perfil in Path(caminho).iterdir():
                if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                if not perfil.is_dir() or perfil.is_symlink() or perfil.is_junction(): continue
                subpastas = ["Cache", "Code Cache", "GPUCache", "GrShaderCache", "DawnCache"] if tipo == "chromium_cache" else ["cache2"]
                for sub in subpastas:
                    sub_path = perfil / sub
                    if sub_path.exists() and sub_path.is_dir() and not sub_path.is_symlink() and not sub_path.is_junction():
                        try:
                            for path, is_dir in _enumerar_seguro(str(sub_path), raiz_autorizada, cancel_event):
                                count += 1
                        except OSError:
                            pass
        except JobCancelledError:
            raise
        except Exception: 
            pass
    return count

def _remover_arquivo(filepath: Path, raiz_autorizada: str, cancel_event, increment_callback=None) -> dict:
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
        if increment_callback:
            increment_callback(bytes_removidos=tamanho, processados=1)
        return {"removidos": 1, "ignorados": 0, "bytes": tamanho}
    except JobCancelledError:
        raise
    except Exception:
        return {"removidos": 0, "ignorados": 1, "bytes": 0}

def _remover_diretorio_recursivo(dirpath: Path, raiz_autorizada: str, cancel_event, increment_callback=None) -> dict:
    from modules.core.exceptions import JobCancelledError
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()
        
    total = {"removidos": 0, "ignorados": 0, "bytes": 0, "erros": []}
    
    try:
        if not dirpath.exists() or dirpath.is_symlink() or dirpath.is_junction() or _is_reparse_point(dirpath):
            return total
            
        if not is_safe_path(str(dirpath), raiz_autorizada):
            return total
            
        entradas = list(_enumerar_seguro(str(dirpath), raiz_autorizada, cancel_event))
        entradas.sort(key=lambda x: len(x[0]), reverse=True)
        
        for item_path, is_dir in entradas:
            if cancel_event and cancel_event.is_set():
                raise JobCancelledError()
                
            item = Path(item_path)
            try:
                if not is_safe_path(str(item), raiz_autorizada):
                    total["ignorados"] += 1
                    total["erros"].append(f"Caminho inseguro: {item}")
                    continue
                    
                if not is_dir:
                    res = _remover_arquivo(item, raiz_autorizada, cancel_event, increment_callback)
                    total["removidos"] += res["removidos"]
                    total["ignorados"] += res["ignorados"]
                    total["bytes"] += res["bytes"]
                    if res["ignorados"] > 0:
                        total["erros"].append(f"Não removido: {item}")
                else:
                    try:
                        item.rmdir()
                    except OSError:
                        pass
            except JobCancelledError:
                raise
            except Exception as e:
                total["ignorados"] += 1
                total["erros"].append(f"Erro ao processar: {item}")
                
    except JobCancelledError:
        raise
    except Exception as e:
        total["ignorados"] += 1
        total["erros"].append(f"Erro em diretório {dirpath}: {str(e)}")
        
    return total

def _processar_alvo(cat_id: str, info: dict, cancel_event, increment_callback=None) -> dict:
    from modules.core.exceptions import JobCancelledError
    tipo = info.get("tipo")
    caminho_base = info.get("caminho", "")
    raiz_autorizada = info.get("raiz_autorizada", "")
    
    total = {"removidos": 0, "ignorados": 0, "bytes": 0, "erros": []}
    
    if tipo == "lixeira":
        try:
            import ctypes
            SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
            res = SHEmptyRecycleBin(None, None, 7)
            if res == 0:
                total["removidos"] = 1
            else:
                total["ignorados"] = 1
                total["erros"].append(f"Código de erro da lixeira: {res}")
        except Exception as e:
            total["ignorados"] = 1
            total["erros"].append(f"Erro ao esvaziar lixeira: {str(e)}")
        return total
        
    if not os.path.exists(caminho_base) or not raiz_autorizada:
        return total
        
    if tipo == "diretorio":
        total = _remover_diretorio_recursivo(Path(caminho_base), raiz_autorizada, cancel_event, increment_callback)
    
    elif tipo == "glob":
        try:
            if is_safe_path(caminho_base, raiz_autorizada):
                for filepath in Path(caminho_base).glob(info["padrao"]):
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    if not is_safe_path(str(filepath), raiz_autorizada): continue
                    if filepath.is_file():
                        res = _remover_arquivo(filepath, raiz_autorizada, cancel_event, increment_callback)
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
                if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                if not perfil.is_dir() or perfil.is_symlink() or perfil.is_junction():
                    continue
                subpastas = ["Cache", "Code Cache", "GPUCache", "GrShaderCache", "DawnCache"]
                for sub in subpastas:
                    sub_path = perfil / sub
                    if sub_path.exists() and sub_path.is_dir() and not sub_path.is_symlink() and not sub_path.is_junction():
                        res = _remover_diretorio_recursivo(sub_path, raiz_autorizada, cancel_event, increment_callback)
                        total["removidos"] += res.get("removidos", 0)
                        total["ignorados"] += res.get("ignorados", 0)
                        total["bytes"] += res.get("bytes", 0)
                        total["erros"].extend(res.get("erros", []))
        except JobCancelledError:
            raise
        except Exception as e:
            total["ignorados"] += 1
            total["erros"].append(f"Erro na iteração Chromium: {str(e)}")
                        
    elif tipo == "firefox_cache":
        try:
            for perfil in Path(caminho_base).iterdir():
                if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                if not perfil.is_dir() or perfil.is_symlink() or perfil.is_junction():
                    continue
                sub_path = perfil / "cache2"
                if sub_path.exists() and sub_path.is_dir() and not sub_path.is_symlink() and not sub_path.is_junction():
                    res = _remover_diretorio_recursivo(sub_path, raiz_autorizada, cancel_event, increment_callback)
                    total["removidos"] += res.get("removidos", 0)
                    total["ignorados"] += res.get("ignorados", 0)
                    total["bytes"] += res.get("bytes", 0)
                    total["erros"].extend(res.get("erros", []))
        except JobCancelledError:
            raise
        except Exception as e:
            total["ignorados"] += 1
            total["erros"].append(f"Erro na iteração Firefox: {str(e)}")

    return total

def executar_limpeza(progress_callback=None, cancel_event=None, incluir_lixeira=False, injetar_alvos=None) -> dict:
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
    
    total_arquivos = 0
    if progress_callback:
        progress_callback(
            mensagem="Contando arquivos...",
            progresso=0,
            detalhes={"categoria": "Preparando", "categoria_percentual": 0, "arquivos_processados": 0, "espaco_liberado_mb": 0.0}
        )
        for _, info in alvos.items():
            total_arquivos += _contar_alvo(info, cancel_event)
            
    total_categorias = len(alvos)
    arquivos_processados = 0
    
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
        
        cb_bytes = 0
        def cb_increment(bytes_removidos=0, processados=0):
            nonlocal arquivos_processados, cb_bytes
            arquivos_processados += processados
            cb_bytes += bytes_removidos
            if progress_callback:
                if total_arquivos > 0:
                    prog = int((arquivos_processados / total_arquivos) * 100)
                else:
                    prog = int((i / total_categorias) * 100) if total_categorias else 100
                progress_callback(
                    mensagem=f"Limpando: {info['nome']}",
                    progresso=min(99, prog),
                    detalhes={
                        "categoria": info["nome"],
                        "categoria_percentual": 0,
                        "arquivos_processados": arquivos_processados,
                        "espaco_liberado_mb": bytes_to_mb(resultado["espaco_liberado_bytes"] + cb_bytes)
                    }
                )
        
        if progress_callback:
            prog = int((arquivos_processados / total_arquivos) * 100) if total_arquivos > 0 else int((i / total_categorias) * 100) if total_categorias else 100
            progress_callback(
                mensagem=f"Limpando: {info['nome']}",
                progresso=min(99, prog),
                detalhes={
                    "categoria": info["nome"],
                    "categoria_percentual": 0,
                    "arquivos_processados": arquivos_processados,
                    "espaco_liberado_mb": bytes_to_mb(resultado["espaco_liberado_bytes"])
                }
            )
            
        cat_result["status"] = "limpando"
        
        try:
            stats = _processar_alvo(cat_id, info, cancel_event, increment_callback=cb_increment)
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
