import json
import logging
import os
import threading
from modules.shared import CACHE_DIR

logger = logging.getLogger(__name__)

CACHE_FILE = CACHE_DIR / "hardware.json"
_cache_lock = threading.Lock()

def _has_dynamic_metrics(obj, path=""):
    BLOCKED = {
        "uso_percentual", "temperatura_c", "frequencia_atual_mhz", "uso_por_nucleo",
        "vram_usada_mb", "leitura_mb_s", "escrita_mb_s", "uptime", "ram_percent", "cpu_percent"
    }
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in BLOCKED:
                return True
            if k == "percentual_uso" and not path.endswith("armazenamento.volumes"):
                return True
            if _has_dynamic_metrics(v, f"{path}.{k}" if path else k):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _has_dynamic_metrics(item, path):
                return True
    return False

def _strip_gpu_capacities(inventario):
    # Não persiste no cache
    if "capacidades" in inventario:
        for k in ["metricas_gpu_disponiveis", "temperatura_gpu_disponivel", "vram_gpu_disponivel"]:
            inventario["capacidades"].pop(k, None)

def carregar_cache_estatico() -> dict:
    """Carrega o inventário do cache de forma segura. Ignora caches de versão antiga ou com métricas."""
    with _cache_lock:
        if not CACHE_FILE.exists():
            return None
            
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if data.get("schema_version") != 2:
                return None
                
            if _has_dynamic_metrics(data):
                logger.warning("Cache rejeitado: contém métricas dinâmicas recursivas.")
                return None
                    
            return data
        except Exception as e:
            logger.warning(f"Falha ao carregar cache de hardware: {e}")
            return None

def salvar_cache_estatico(inventario: dict) -> bool:
    """Salva o inventário atomicamente. Impede salvar se contiver métricas."""
    if inventario.get("schema_version") != 2:
        return False
        
    if _has_dynamic_metrics(inventario):
        raise ValueError("Tentativa de salvar métricas dinâmicas no cache")

    import copy
    inv_to_save = copy.deepcopy(inventario)
    _strip_gpu_capacities(inv_to_save)

    with _cache_lock:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            temp_file = str(CACHE_FILE) + ".tmp"
            
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(inv_to_save, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
                
            os.replace(temp_file, str(CACHE_FILE))
            return True
        except Exception as e:
            logger.warning(f"Falha ao salvar cache de hardware: {e}")
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
            return False

def deletar_cache():
    with _cache_lock:
        try:
            if CACHE_FILE.exists():
                CACHE_FILE.unlink()
        except Exception:
            pass
