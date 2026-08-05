import os
import stat
import time
import fnmatch
from pathlib import Path

def bytes_to_mb(valor: int) -> float:
    return round(valor / (1024 ** 2), 2)

def is_safe_path(caminho: str, raiz_autorizada: str) -> bool:
    try:
        real_path = os.path.normcase(os.path.normpath(os.path.realpath(caminho)))
        real_root = os.path.normcase(os.path.normpath(os.path.realpath(raiz_autorizada)))
        return os.path.commonpath([real_path, real_root]) == real_root
    except ValueError:
        return False
    except OSError:
        return False

def _is_reparse_point(filepath: Path, st=None) -> bool:
    from modules.core.exceptions import JobCancelledError
    try:
        if st is None:
            st = os.lstat(str(filepath))
        return bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except AttributeError:
        return filepath.is_symlink() or (hasattr(filepath, 'is_junction') and filepath.is_junction())
    except JobCancelledError:
        raise
    except OSError:
        return True

def _classificar_item_navegador(p: Path, st=None) -> bool:
    """
    Retorna True se o item deve ser ignorado por ser link ou reparse point.
    """
    if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) or _is_reparse_point(p, st):
        return True
    return False

def _enumerar_seguro(caminho: str, raiz_autorizada: str, cancel_event, on_error=None):
    from modules.core.exceptions import JobCancelledError
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()

    try:
        it = os.scandir(caminho)
    except OSError as exc:
        if on_error:
            nome = os.path.basename(caminho) or caminho
            on_error(f"Falha de acesso em diretório: {nome} ({type(exc).__name__})")
        return

    with it:
        for entry in it:
            if cancel_event and cancel_event.is_set():
                raise JobCancelledError()

            p = Path(entry.path)
            try:
                st = entry.stat(follow_symlinks=False)
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError as exc:
                if on_error:
                    on_error(f"Falha de acesso em item: {entry.name} ({type(exc).__name__})")
                continue

            if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) or _is_reparse_point(p, st):
                if on_error:
                    on_error(f"Link ou reparse point ignorado: {entry.name}")
                continue

            if not is_safe_path(entry.path, raiz_autorizada):
                if on_error:
                    on_error(f"Caminho inseguro ignorado: {entry.name}")
                continue

            if is_dir:
                yield from _enumerar_seguro(entry.path, raiz_autorizada, cancel_event, on_error)
                yield entry.path, True
            else:
                yield entry.path, False

def _enumerar_glob_seguro(caminho_base: str, padrao: str, raiz_autorizada: str, cancel_event, on_error=None):
    from modules.core.exceptions import JobCancelledError
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()

    try:
        it = os.scandir(caminho_base)
    except OSError as exc:
        if on_error:
            nome = os.path.basename(caminho_base) or caminho_base
            on_error(f"Falha de acesso na raiz glob: {nome} ({type(exc).__name__})")
        return

    with it:
        for entry in it:
            if cancel_event and cancel_event.is_set():
                raise JobCancelledError()

            if not fnmatch.fnmatch(entry.name, padrao):
                continue

            p = Path(entry.path)
            try:
                st = entry.stat(follow_symlinks=False)
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError as exc:
                if on_error:
                    on_error(f"Falha de acesso em item glob: {entry.name} ({type(exc).__name__})")
                continue

            if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) or _is_reparse_point(p, st):
                if on_error:
                    on_error(f"Link ou reparse point ignorado (glob): {entry.name}")
                continue

            if not is_safe_path(entry.path, raiz_autorizada):
                if on_error:
                    on_error(f"Caminho inseguro ignorado (glob): {entry.name}")
                continue

            yield entry.path, is_dir

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

class ProgressTracker:
    def __init__(self, callback):
        self.callback = callback
        self.total_arquivos = 0
        self.arquivos_processados = 0
        self.arquivos_removidos = 0
        self.arquivos_ignorados = 0
        self.espaco_liberado_bytes = 0

        self.categorias = []
        self.cat_map = {}
        self.current_cat = None

        self.last_update_time = 0
        self.items_since_last_update = 0
        self.fase = "contando"

        self.last_snapshot = None

    def add_category(self, cat_id, nome):
        cat = {
            "id": cat_id,
            "nome": nome,
            "status": "aguardando",
            "percentual": 0,
            "arquivos_removidos": 0,
            "arquivos_ignorados": 0,
            "arquivos_total": 0,
            "processados_na_categoria": 0,
            "espaco_liberado_bytes": 0
        }
        self.categorias.append(cat)
        self.cat_map[cat_id] = cat
        return cat

    def set_fase(self, fase):
        self.fase = fase
        self.force_update()

    def start_category(self, cat_id):
        if self.current_cat and self.current_cat["status"] == "limpando":
            if self.current_cat["arquivos_ignorados"] > 0:
                self.current_cat["status"] = "parcial"
            else:
                self.current_cat["status"] = "concluido"
            self.current_cat["percentual"] = 100

        self.current_cat = self.cat_map[cat_id]
        if self.fase == "limpando":
            self.current_cat["status"] = "limpando"
        self.force_update()

    def add_count(self, cat_id):
        self.cat_map[cat_id]["arquivos_total"] += 1
        self.total_arquivos += 1

    def increment_processed(self, cat_id, removed=0, ignored=0, bytes_liberados=0):
        self.arquivos_processados += (removed + ignored)
        self.arquivos_removidos += removed
        self.arquivos_ignorados += ignored
        self.espaco_liberado_bytes += bytes_liberados

        cat = self.cat_map[cat_id]
        cat["arquivos_removidos"] += removed
        cat["arquivos_ignorados"] += ignored
        cat["processados_na_categoria"] += (removed + ignored)
        cat["espaco_liberado_bytes"] += bytes_liberados

        self.items_since_last_update += (removed + ignored)

        now = time.time()
        if (now - self.last_update_time >= 0.15) or (self.items_since_last_update >= 50):
            self.emit_update()

    def force_update(self):
        self.emit_update()

    def emit_update(self):
        self.last_update_time = time.time()
        self.items_since_last_update = 0

        prog_geral = 0
        if self.fase == "limpando":
            prog_geral = int((self.arquivos_processados / self.total_arquivos) * 100) if self.total_arquivos > 0 else 0
            prog_geral = min(99, max(0, prog_geral))
        elif self.fase == "concluido":
            prog_geral = 100

        if self.current_cat and self.fase == "limpando":
            c_total = self.current_cat["arquivos_total"]
            c_proc = self.current_cat["processados_na_categoria"]
            c_prog = int((c_proc / c_total) * 100) if c_total > 0 else 0
            self.current_cat["percentual"] = min(99, max(0, c_prog))

        snapshot = {
            "fase": self.fase,
            "categoria_id": self.current_cat["id"] if self.current_cat else "",
            "categoria": self.current_cat["nome"] if self.current_cat else "",
            "categoria_percentual": self.current_cat["percentual"] if self.current_cat else 0,
            "arquivos_processados": self.arquivos_processados,
            "arquivos_total": self.total_arquivos,
            "arquivos_removidos": self.arquivos_removidos,
            "arquivos_ignorados": self.arquivos_ignorados,
            "espaco_liberado_bytes": self.espaco_liberado_bytes,
            "espaco_liberado_mb": bytes_to_mb(self.espaco_liberado_bytes),
            "categorias": self.categorias
        }
        self.last_snapshot = snapshot

        if self.callback:
            msg = "Contando arquivos..." if self.fase == "contando" else f"Limpando: {snapshot['categoria']}" if self.fase == "limpando" else "Concluído"
            self.callback(mensagem=msg, progresso=prog_geral, detalhes=snapshot)

    def finish(self, success=True):
        self.fase = "concluido" if success else "falhou"
        if self.current_cat:
            if self.fase == "concluido":
                self.current_cat["status"] = "parcial" if self.current_cat["arquivos_ignorados"] > 0 else "concluido"
            else:
                self.current_cat["status"] = "falhou"
            self.current_cat["percentual"] = 100
        self.force_update()

def _contar_alvo(cat_id: str, info: dict, tracker: ProgressTracker, cancel_event) -> None:
    from modules.core.exceptions import JobCancelledError
    tipo = info.get("tipo")
    if tipo == "lixeira":
        tracker.add_count(cat_id)
        return

    caminho = info.get("caminho")
    if not caminho or not os.path.exists(caminho): return
    raiz_autorizada = info.get("raiz_autorizada")
    if not raiz_autorizada: return

    def on_error(msg):
        tracker.add_count(cat_id)

    if tipo == "diretorio":
        for path, is_dir in _enumerar_seguro(caminho, raiz_autorizada, cancel_event, on_error):
            tracker.add_count(cat_id)

    elif tipo == "glob":
        if is_safe_path(caminho, raiz_autorizada):
            for path, is_dir in _enumerar_glob_seguro(caminho, info["padrao"], raiz_autorizada, cancel_event, on_error):
                tracker.add_count(cat_id)

    elif tipo in ("chromium_cache", "firefox_cache"):
        try:
            with os.scandir(caminho) as it:
                for perfil in it:
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    try:
                        st = perfil.stat(follow_symlinks=False)
                        p = Path(perfil.path)
                        if _classificar_item_navegador(p, st):
                            on_error("Perfil ignorado (link/reparse)")
                            continue
                        if not stat.S_ISDIR(st.st_mode):
                            continue
                        if not is_safe_path(str(p), raiz_autorizada):
                            on_error("Perfil inseguro")
                            continue
                    except OSError:
                        on_error("Erro no perfil")
                        continue

                    subpastas = ["Cache", "Code Cache", "GPUCache", "GrShaderCache", "DawnCache"] if tipo == "chromium_cache" else ["cache2"]
                    for sub in subpastas:
                        sub_path = p / sub
                        try:
                            if sub_path.exists():
                                if _classificar_item_navegador(sub_path):
                                    on_error("Subpasta ignorada (link/reparse)")
                                    continue
                                if sub_path.is_dir():
                                    if not is_safe_path(str(sub_path), raiz_autorizada):
                                        on_error("Subpasta insegura")
                                        continue
                                    for path, is_item_dir in _enumerar_seguro(str(sub_path), raiz_autorizada, cancel_event, on_error):
                                        tracker.add_count(cat_id)
                        except OSError:
                            on_error("Erro no cache subpasta")
        except JobCancelledError:
            raise
        except OSError:
            on_error("Erro raiz navegador")

def _remover_arquivo(filepath: Path, raiz_autorizada: str, cancel_event, on_error) -> dict:
    from modules.core.exceptions import JobCancelledError
    try:
        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()

        if not is_safe_path(str(filepath), raiz_autorizada):
            on_error("Caminho inseguro")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        st1 = os.lstat(str(filepath))
        if stat.S_ISLNK(st1.st_mode) or _is_reparse_point(filepath, st1):
            on_error("Reparse point")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        tamanho = st1.st_size

        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()

        st2 = os.lstat(str(filepath))
        if (st1.st_ino != st2.st_ino or
            st1.st_dev != st2.st_dev or
            st1.st_size != st2.st_size or
            st1.st_mode != st2.st_mode):
            on_error("TOCTOU mismatch")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        if stat.S_ISLNK(st2.st_mode) or _is_reparse_point(filepath, st2):
            on_error("Reparse point 2")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        if not is_safe_path(str(filepath), raiz_autorizada):
            on_error("Caminho inseguro 2")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()

        filepath.unlink()
        return {"removidos": 1, "ignorados": 0, "bytes": tamanho}
    except JobCancelledError:
        raise
    except OSError as e:
        on_error(f"Erro ao remover arquivo: {type(e).__name__}")
        return {"removidos": 0, "ignorados": 1, "bytes": 0}

def _remover_diretorio(dirpath: Path, raiz_autorizada: str, cancel_event, on_error) -> dict:
    from modules.core.exceptions import JobCancelledError
    try:
        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()

        st1 = os.lstat(str(dirpath))
        if stat.S_ISLNK(st1.st_mode) or _is_reparse_point(dirpath, st1):
            on_error("Reparse point dir")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        if not is_safe_path(str(dirpath), raiz_autorizada):
            on_error("Caminho inseguro dir")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        st2 = os.lstat(str(dirpath))
        if (st1.st_ino != st2.st_ino or
            st1.st_dev != st2.st_dev or
            st1.st_size != st2.st_size or
            st1.st_mode != st2.st_mode):
            on_error("TOCTOU mismatch dir")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        if stat.S_ISLNK(st2.st_mode) or _is_reparse_point(dirpath, st2):
            on_error("Reparse point dir 2")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        if not is_safe_path(str(dirpath), raiz_autorizada):
            on_error("Caminho inseguro dir 2")
            return {"removidos": 0, "ignorados": 1, "bytes": 0}

        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()

        dirpath.rmdir()
        return {"removidos": 1, "ignorados": 0, "bytes": 0}
    except JobCancelledError:
        raise
    except OSError as e:
        on_error(f"Erro ao remover dir: {type(e).__name__}")
        return {"removidos": 0, "ignorados": 1, "bytes": 0}

def _remover_diretorio_recursivo(dirpath: Path, raiz_autorizada: str, cat_id: str, tracker: ProgressTracker, cancel_event, avisos_ref: list) -> None:
    from modules.core.exceptions import JobCancelledError
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()

    def on_error(msg):
        tracker.increment_processed(cat_id, removed=0, ignored=1, bytes_liberados=0)
        avisos_ref.append(msg)

    def log_error(msg):
        avisos_ref.append(msg)

    try:
        if not dirpath.exists():
            return

        if dirpath.is_symlink() or (hasattr(dirpath, 'is_junction') and dirpath.is_junction()) or _is_reparse_point(dirpath):
            on_error(f"Diretório raiz ignorado (link/reparse): {dirpath.name}")
            return

        if not is_safe_path(str(dirpath), raiz_autorizada):
            on_error(f"Diretório raiz inseguro: {dirpath.name}")
            return

        for item_path, is_dir in _enumerar_seguro(str(dirpath), raiz_autorizada, cancel_event, on_error):
            if cancel_event and cancel_event.is_set():
                raise JobCancelledError()

            item = Path(item_path)
            try:
                if not is_dir:
                    res = _remover_arquivo(item, raiz_autorizada, cancel_event, log_error)
                    tracker.increment_processed(cat_id, removed=res["removidos"], ignored=res["ignorados"], bytes_liberados=res["bytes"])
                else:
                    res = _remover_diretorio(item, raiz_autorizada, cancel_event, log_error)
                    tracker.increment_processed(cat_id, removed=res["removidos"], ignored=res["ignorados"], bytes_liberados=res["bytes"])
            except JobCancelledError:
                raise
            except OSError as e:
                on_error(f"Erro inesperado: {type(e).__name__}")

    except JobCancelledError:
        raise
    except OSError as e:
        on_error(f"Erro em diretório raiz: {type(e).__name__}")

def _processar_alvo(cat_id: str, info: dict, tracker: ProgressTracker, cancel_event, avisos_ref: list) -> None:
    from modules.core.exceptions import JobCancelledError
    tipo = info.get("tipo")
    caminho_base = info.get("caminho", "")
    raiz_autorizada = info.get("raiz_autorizada", "")

    def on_error(msg):
        tracker.increment_processed(cat_id, removed=0, ignored=1, bytes_liberados=0)
        avisos_ref.append(msg)

    def log_error(msg):
        avisos_ref.append(msg)

    if tipo == "lixeira":
        try:
            import ctypes
            SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
            res = SHEmptyRecycleBin(None, None, 7)
            if res == 0:
                tracker.increment_processed(cat_id, removed=1, ignored=0, bytes_liberados=0)
            else:
                on_error(f"Código lixeira: {res}")
        except JobCancelledError:
            raise
        except OSError as e:
            on_error(f"Erro lixeira ({type(e).__name__})")
        return

    if not os.path.exists(caminho_base) or not raiz_autorizada:
        return

    if tipo == "diretorio":
        _remover_diretorio_recursivo(Path(caminho_base), raiz_autorizada, cat_id, tracker, cancel_event, avisos_ref)

    elif tipo == "glob":
        try:
            if is_safe_path(caminho_base, raiz_autorizada):
                for filepath_str, is_dir in _enumerar_glob_seguro(caminho_base, info["padrao"], raiz_autorizada, cancel_event, on_error):
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    if not is_dir:
                        res = _remover_arquivo(Path(filepath_str), raiz_autorizada, cancel_event, log_error)
                        tracker.increment_processed(cat_id, removed=res["removidos"], ignored=res["ignorados"], bytes_liberados=res["bytes"])
        except JobCancelledError:
            raise
        except OSError as e:
            on_error(f"Erro no glob ({type(e).__name__})")

    elif tipo == "chromium_cache":
        try:
            with os.scandir(caminho_base) as it:
                for perfil in it:
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    try:
                        st = perfil.stat(follow_symlinks=False)
                        p = Path(perfil.path)

                        if _classificar_item_navegador(p, st):
                            on_error(f"Perfil ignorado (link/reparse): {perfil.name}")
                            continue

                        if not stat.S_ISDIR(st.st_mode):
                            continue
                            
                        if not is_safe_path(str(p), raiz_autorizada):
                            on_error(f"Perfil inseguro: {perfil.name}")
                            continue
                    except OSError as e:
                        on_error(f"Erro lendo perfil Chromium ({type(e).__name__})")
                        continue

                    subpastas = ["Cache", "Code Cache", "GPUCache", "GrShaderCache", "DawnCache"]
                    for sub in subpastas:
                        sub_path = p / sub
                        try:
                            if sub_path.exists():
                                if _classificar_item_navegador(sub_path):
                                    on_error(f"Subpasta ignorada (link/reparse): {sub}")
                                    continue
                                if sub_path.is_dir():
                                    if not is_safe_path(str(sub_path), raiz_autorizada):
                                        on_error(f"Subpasta insegura: {sub}")
                                        continue
                                    _remover_diretorio_recursivo(sub_path, raiz_autorizada, cat_id, tracker, cancel_event, avisos_ref)
                        except OSError as e:
                            on_error(f"Erro no subdiretório {sub} ({type(e).__name__})")
        except JobCancelledError:
            raise
        except OSError as e:
            on_error(f"Erro Chromium ({type(e).__name__})")

    elif tipo == "firefox_cache":
        try:
            with os.scandir(caminho_base) as it:
                for perfil in it:
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    try:
                        st = perfil.stat(follow_symlinks=False)
                        p = Path(perfil.path)

                        if _classificar_item_navegador(p, st):
                            on_error(f"Perfil ignorado (link/reparse): {perfil.name}")
                            continue

                        if not stat.S_ISDIR(st.st_mode):
                            continue
                            
                        if not is_safe_path(str(p), raiz_autorizada):
                            on_error(f"Perfil inseguro: {perfil.name}")
                            continue
                    except OSError as e:
                        on_error(f"Erro lendo perfil Firefox ({type(e).__name__})")
                        continue

                    sub_path = p / "cache2"
                    try:
                        if sub_path.exists():
                            if _classificar_item_navegador(sub_path):
                                on_error(f"Subpasta ignorada (link/reparse): cache2")
                                continue
                            if sub_path.is_dir():
                                if not is_safe_path(str(sub_path), raiz_autorizada):
                                    on_error(f"Subpasta insegura: cache2")
                                    continue
                                _remover_diretorio_recursivo(sub_path, raiz_autorizada, cat_id, tracker, cancel_event, avisos_ref)
                    except OSError as e:
                        on_error(f"Erro no cache2 ({type(e).__name__})")
        except JobCancelledError:
            raise
        except OSError as e:
            on_error(f"Erro Firefox ({type(e).__name__})")

def executar_limpeza(progress_callback=None, cancel_event=None, incluir_lixeira=False, injetar_alvos=None) -> dict:
    from modules.core.exceptions import JobCancelledError

    if injetar_alvos is not None:
        for k, v in injetar_alvos.items():
            if v.get("tipo") != "lixeira" and "raiz_autorizada" not in v:
                raise ValueError(f"Alvo injetado '{k}' sem raiz_autorizada")
        alvos = injetar_alvos
    else:
        alvos = _obter_alvos_limpeza(incluir_lixeira=incluir_lixeira)

    tracker = ProgressTracker(progress_callback)
    for cat_id, info in alvos.items():
        tracker.add_category(cat_id, info["nome"])

    tracker.set_fase("contando")
    for cat_id, info in alvos.items():
        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()
        tracker.start_category(cat_id)
        _contar_alvo(cat_id, info, tracker, cancel_event)

    tracker.set_fase("limpando")

    global_avisos = []

    for cat_id, info in alvos.items():
        if cancel_event and cancel_event.is_set():
            raise JobCancelledError()

        tracker.start_category(cat_id)

        cat_avisos = []
        try:
            _processar_alvo(cat_id, info, tracker, cancel_event, cat_avisos)
            if cat_avisos:
                global_avisos.append(f"Erros em {info['nome']}: {'; '.join(cat_avisos[:5])}")

        except JobCancelledError:
            tracker.finish(success=False)
            raise
        except OSError as e:
            global_avisos.append(f"Falha total em {info['nome']}: ({type(e).__name__})")
            cat = tracker.cat_map[cat_id]
            cat["status"] = "falhou"
            tracker.force_update()

    tracker.finish(success=True)

    res_snapshot = tracker.last_snapshot or {}

    parcial = any(c["status"] in ("parcial", "falhou") for c in tracker.categorias)

    return {
        "ok": True,
        "parcial": parcial,
        "espaco_liberado_bytes": tracker.espaco_liberado_bytes,
        "espaco_liberado_mb": bytes_to_mb(tracker.espaco_liberado_bytes),
        "arquivos_removidos": tracker.arquivos_removidos,
        "arquivos_ignorados": tracker.arquivos_ignorados,
        "categorias": tracker.categorias,
        "avisos": global_avisos,
        "resultado_parcial": res_snapshot
    }
