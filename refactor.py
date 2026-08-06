import re

with open(r"c:\Users\Thiago\Desktop\projetos\phoenix-optimizer\modules\core\cleanup_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add imports and RootValidation
imports = """import os
import stat
import time
import fnmatch
from pathlib import Path
from dataclasses import dataclass

from modules.core.exceptions import JobCancelledError, RootChangedError
from modules.core.windows_known_folders import obter_local_appdata, obter_windows_directory

@dataclass
class RootValidation:
    caminho_normalizado: str
    realpath: str
    st_dev: int
    st_ino: int
    st_mode: int
    st_file_attributes: int

def _safe_scandir(caminho: str, raiz_autorizada: str, cancel_event, root_val: RootValidation):
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()
        
    try:
        st2 = os.lstat(caminho)
    except OSError:
        raise RootChangedError("Raiz do alvo inacessível")
        
    if (st2.st_ino != root_val.st_ino or 
        st2.st_dev != root_val.st_dev or 
        st2.st_mode != root_val.st_mode):
        raise RootChangedError("Raiz alterada durante a operação")
        
    p = Path(caminho)
    if _classificar_item_navegador(p, st2):
        raise RootChangedError("Link ou reparse point ignorado")
        
    if not is_safe_path(caminho, raiz_autorizada):
        raise RootChangedError("Caminho inseguro ignorado")
        
    try:
        return os.scandir(caminho)
    except OSError:
        raise RootChangedError("Raiz do alvo inacessível")
"""
content = re.sub(r"import os\nimport stat\nimport time\nimport fnmatch\nfrom pathlib import Path\n", imports, content)

# 2. Update _validar_raiz
validar_raiz = """def _validar_raiz(caminho: str, raiz_autorizada: str, cancel_event, on_error=None) -> RootValidation:
    if cancel_event and cancel_event.is_set():
        raise JobCancelledError()
    
    try:
        st = os.lstat(caminho)
    except OSError:
        if on_error:
            on_error("Raiz do alvo inacessível")
        return None

    p = Path(caminho)
    if _classificar_item_navegador(p, st):
        if on_error:
            on_error("Link ou reparse point ignorado")
        return None

    if not is_safe_path(caminho, raiz_autorizada):
        if on_error:
            on_error("Caminho inseguro ignorado")
        return None
        
    try:
        real_path = os.path.normcase(os.path.normpath(os.path.realpath(caminho)))
        norm_path = os.path.normcase(os.path.normpath(caminho))
    except (OSError, ValueError):
        if on_error:
            on_error("Raiz do alvo inacessível")
        return None

    return RootValidation(
        caminho_normalizado=norm_path,
        realpath=real_path,
        st_dev=st.st_dev,
        st_ino=st.st_ino,
        st_mode=st.st_mode,
        st_file_attributes=getattr(st, 'st_file_attributes', 0)
    )"""
content = re.sub(r"def _validar_raiz\(.*?\n        return True", validar_raiz, content, flags=re.DOTALL)

# 3. Update _enumerar_seguro
enumerar_seguro = """def _enumerar_seguro(caminho: str, raiz_autorizada: str, cancel_event, on_error=None, root_val: RootValidation=None):
    if root_val is None:
        return
        
    it = _safe_scandir(caminho, raiz_autorizada, cancel_event, root_val)

    with it:
        for entry in it:
            if cancel_event and cancel_event.is_set():
                raise JobCancelledError()

            p = Path(entry.path)
            try:
                st = entry.stat(follow_symlinks=False)
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                if on_error:
                    on_error("Falha de acesso em item")
                continue

            if _classificar_item_navegador(p, st):
                if on_error:
                    on_error("Link ou reparse point ignorado")
                continue

            if not is_safe_path(entry.path, raiz_autorizada):
                if on_error:
                    on_error("Caminho inseguro ignorado")
                continue

            if is_dir:
                val_sub = _validar_raiz(entry.path, raiz_autorizada, cancel_event, on_error)
                if val_sub:
                    try:
                        yield from _enumerar_seguro(entry.path, raiz_autorizada, cancel_event, on_error, val_sub)
                    except RootChangedError as e:
                        if on_error: on_error(str(e))
                yield entry.path, True
            else:
                yield entry.path, False"""
content = re.sub(r"def _enumerar_seguro\(.*?\n                yield entry.path, False", enumerar_seguro, content, flags=re.DOTALL)

# 4. Update _enumerar_glob_seguro
enumerar_glob_seguro = """def _enumerar_glob_seguro(caminho_base: str, padrao: str, raiz_autorizada: str, cancel_event, on_error=None, root_val: RootValidation=None):
    if root_val is None:
        return
        
    it = _safe_scandir(caminho_base, raiz_autorizada, cancel_event, root_val)

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
            except OSError:
                if on_error:
                    on_error("Falha de acesso em item glob")
                continue

            if _classificar_item_navegador(p, st):
                if on_error:
                    on_error("Link ou reparse point ignorado")
                continue

            if not is_safe_path(entry.path, raiz_autorizada):
                if on_error:
                    on_error("Caminho inseguro ignorado")
                continue

            yield entry.path, is_dir"""
content = re.sub(r"def _enumerar_glob_seguro\(.*?\n            yield entry.path, is_dir", enumerar_glob_seguro, content, flags=re.DOTALL)

# 5. Update _obter_alvos_limpeza
obter_alvos = """def _obter_alvos_limpeza(incluir_lixeira=False) -> dict:
    local_appdata = obter_local_appdata()
    windows_dir = obter_windows_directory()
    alvos = {}"""
content = re.sub(r"def _obter_alvos_limpeza\(incluir_lixeira=False\) -> dict:\n    local_appdata = os.environ.get\(\"LOCALAPPDATA\", \"\"\)\n    alvos = \{\}\n\n    if local_appdata:\n        temp_user = os.path.join\(local_appdata, \"Temp\"\)\n        alvos\[\"temp_usuario\"\] = \{\n            \"nome\": \"Arquivos temporários do usuário\",\n            \"caminho\": temp_user,\n            \"raiz_autorizada\": local_appdata,\n            \"tipo\": \"diretorio\"\n        \}\n\n    windows_dir = os.environ.get\(\"SystemRoot\", r\"C:\\Windows\"\)\n    alvos\[\"temp_windows\"\]", 
                 """def _obter_alvos_limpeza(incluir_lixeira=False) -> dict:
    local_appdata = obter_local_appdata()
    alvos = {}

    if local_appdata:
        temp_user = os.path.join(local_appdata, "Temp")
        alvos["temp_usuario"] = {
            "nome": "Arquivos temporários do usuário",
            "caminho": temp_user,
            "raiz_autorizada": local_appdata,
            "tipo": "diretorio"
        }

    windows_dir = obter_windows_directory()
    alvos["temp_windows"]""", content)

# 6. Update _contar_alvo
contar_alvo = """def _contar_alvo(cat_id: str, info: dict, tracker: ProgressTracker, cancel_event) -> None:
    tipo = info.get("tipo")
    if tipo == "lixeira":
        tracker.add_count(cat_id)
        return

    caminho = info.get("caminho")
    # Removido os.path.exists
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
                            # Removido sub_path.exists()
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
content = re.sub(r"def _contar_alvo\(.*?\n                        on_error\(\"Erro raiz navegador\"\)", contar_alvo, content, flags=re.DOTALL)


# 7. Update _processar_alvo and friends
# In _processar_alvo, fix os.path.exists and RootChangedError wrapping
content = content.replace("if not os.path.exists(caminho_base) or not raiz_autorizada:\n        return", "if not caminho_base or not raiz_autorizada:\n        return")

# Ensure _remover_diretorio_recursivo signature accepts root_val
content = content.replace("def _remover_diretorio_recursivo(dirpath: Path, raiz_autorizada: str, cat_id: str, tracker: ProgressTracker, cancel_event, avisos_ref: list) -> None:", "def _remover_diretorio_recursivo(dirpath: Path, raiz_autorizada: str, cat_id: str, tracker: ProgressTracker, cancel_event, avisos_ref: list, root_val: RootValidation) -> None:")

# Fix enumerar_seguro call in _remover_diretorio_recursivo
content = content.replace("for item_path, is_dir in _enumerar_seguro(str(dirpath), raiz_autorizada, cancel_event, on_error):", "for item_path, is_dir in _enumerar_seguro(str(dirpath), raiz_autorizada, cancel_event, on_error, root_val):")

# Fix _processar_alvo to catch RootChangedError
processar_alvo_fix = """
    val = _validar_raiz(caminho_base, raiz_autorizada, cancel_event, root_error)
    if not val:
        return
        
    try:
        if tipo == "diretorio":
            _remover_diretorio_recursivo(Path(caminho_base), raiz_autorizada, cat_id, tracker, cancel_event, avisos_ref, val)

        elif tipo == "glob":
            for filepath_str, is_dir in _enumerar_glob_seguro(caminho_base, info["padrao"], raiz_autorizada, cancel_event, on_error, val):
                if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                if not is_dir:
                    res = _remover_arquivo(Path(filepath_str), raiz_autorizada, cancel_event, log_error)
                    tracker.increment_processed(cat_id, removed=res["removidos"], ignored=res["ignorados"], bytes_liberados=res["bytes"])
                    
        elif tipo == "chromium_cache":
            with _safe_scandir(caminho_base, raiz_autorizada, cancel_event, val) as it:
                for perfil in it:
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    try:
                        p = Path(perfil.path)
                        val_perfil = _validar_raiz(str(p), raiz_autorizada, cancel_event, on_error)
                        if not val_perfil: continue
                        if not p.is_dir(): continue
                    except OSError:
                        on_error("Erro lendo perfil Chromium")
                        continue

                    subpastas = ["Cache", "Code Cache", "GPUCache", "GrShaderCache", "DawnCache"]
                    for sub in subpastas:
                        sub_path = p / sub
                        try:
                            val_sub = _validar_raiz(str(sub_path), raiz_autorizada, cancel_event, on_error)
                            if not val_sub: continue
                            if sub_path.is_dir():
                                try:
                                    _remover_diretorio_recursivo(sub_path, raiz_autorizada, cat_id, tracker, cancel_event, avisos_ref, val_sub)
                                except RootChangedError as e:
                                    on_error(str(e))
                        except OSError:
                            on_error("Erro no subdiretório")
                            
        elif tipo == "firefox_cache":
            with _safe_scandir(caminho_base, raiz_autorizada, cancel_event, val) as it:
                for perfil in it:
                    if cancel_event and cancel_event.is_set(): raise JobCancelledError()
                    p = Path(perfil.path)
                    try:
                        val_perfil = _validar_raiz(str(p), raiz_autorizada, cancel_event, on_error)
                        if not val_perfil: continue
                        if not p.is_dir(): continue
                    except OSError:
                        on_error("Erro lendo perfil Firefox")
                        continue

                    sub_path = p / "cache2"
                    try:
                        val_sub = _validar_raiz(str(sub_path), raiz_autorizada, cancel_event, on_error)
                        if not val_sub: continue
                        if sub_path.is_dir():
                            try:
                                _remover_diretorio_recursivo(sub_path, raiz_autorizada, cat_id, tracker, cancel_event, avisos_ref, val_sub)
                            except RootChangedError as e:
                                on_error(str(e))
                    except OSError:
                        on_error("Erro no cache2")
                        
    except RootChangedError as e:
        root_error(str(e))
    except JobCancelledError:
        raise
    except OSError:
        on_error("Erro na raiz do alvo")
"""

content = re.sub(r"\n    if not _validar_raiz\(caminho_base, raiz_autorizada, cancel_event, root_error\):\n        return\n    if tipo == \"diretorio\":.*?    elif tipo == \"firefox_cache\":.*?        except OSError as e:\n            on_error\(f\"Erro Firefox \(\{type\(e\).__name__\}\)\"\)", processar_alvo_fix, content, flags=re.DOTALL)

# Let's fix _remover_diretorio_recursivo to remove .exists() check and update warnings
content = content.replace("if not dirpath.exists():\n            return", "pass")
content = re.sub(r"on_error\(f\"Diretório raiz ignorado \(link/reparse\): \{dirpath.name\}\"\)", "on_error(\"Diretório raiz ignorado (link/reparse)\")", content)
content = re.sub(r"on_error\(f\"Diretório raiz inseguro: \{dirpath.name\}\"\)", "on_error(\"Diretório raiz inseguro\")", content)

with open(r"c:\Users\Thiago\Desktop\projetos\phoenix-optimizer\modules\core\cleanup_service.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
