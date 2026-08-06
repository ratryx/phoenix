import re

with open(r"c:\Users\Thiago\Desktop\projetos\phoenix-optimizer\modules\core\cleanup_service.py", "r", encoding="utf-8") as f:
    content = f.read()

contar_alvo = """def _contar_alvo(cat_id: str, info: dict, tracker: ProgressTracker, cancel_event) -> None:
    from modules.core.exceptions import JobCancelledError
    tipo = info.get("tipo")
    if tipo == "lixeira":
        tracker.add_count(cat_id)
        return

    caminho = info.get("caminho")
    if not caminho: return
    raiz_autorizada = info.get("raiz_autorizada")
    if not raiz_autorizada: return

    def on_error(msg):
        tracker.add_count(cat_id)

    val = _validar_raiz(caminho, raiz_autorizada, cancel_event, on_error)
    if not val:
        tracker.add_count(cat_id)
        return

    try:
        if tipo == "diretorio":
            for path, is_dir in _enumerar_seguro(caminho, raiz_autorizada, cancel_event, on_error, val):
                tracker.add_count(cat_id)

        elif tipo == "glob":
            for path, is_dir in _enumerar_glob_seguro(caminho, info["padrao"], raiz_autorizada, cancel_event, on_error, val):
                tracker.add_count(cat_id)

        elif tipo in ("chromium_cache", "firefox_cache"):
            with _safe_scandir(caminho, raiz_autorizada, cancel_event, val) as it:
                for perfil in it:
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    try:
                        p = Path(perfil.path)
                        val_perfil = _validar_raiz(str(p), raiz_autorizada, cancel_event, on_error)
                        if not val_perfil: continue
                        if not p.is_dir(): continue
                    except OSError:
                        on_error("Erro no perfil")
                        continue

                    subpastas = ["Cache", "Code Cache", "GPUCache", "GrShaderCache", "DawnCache"] if tipo == "chromium_cache" else ["cache2"]
                    for sub in subpastas:
                        sub_path = p / sub
                        try:
                            val_sub = _validar_raiz(str(sub_path), raiz_autorizada, cancel_event, on_error)
                            if not val_sub: continue
                            if sub_path.is_dir():
                                try:
                                    for path, is_item_dir in _enumerar_seguro(str(sub_path), raiz_autorizada, cancel_event, on_error, val_sub):
                                        tracker.add_count(cat_id)
                                except RootChangedError as e:
                                    on_error(str(e))
                                    tracker.add_count(cat_id)
                        except OSError:
                            on_error("Erro no cache subpasta")
    except RootChangedError as e:
        on_error(str(e))
        tracker.add_count(cat_id)
    except JobCancelledError:
        raise
    except OSError:
        on_error("Erro raiz navegador")"""

content = re.sub(r"def _contar_alvo\(cat_id: str, info: dict, tracker: ProgressTracker, cancel_event\) -> None:.*?on_error\(\"Erro raiz navegador\"\)", contar_alvo, content, flags=re.DOTALL)

with open(r"c:\Users\Thiago\Desktop\projetos\phoenix-optimizer\modules\core\cleanup_service.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
