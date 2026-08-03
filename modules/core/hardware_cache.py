import json
import logging
import os
import threading
from modules.shared import CACHE_DIR

logger = logging.getLogger(__name__)

CACHE_FILE = CACHE_DIR / "hardware.json"
_cache_lock = threading.Lock()

def carregar_cache_estatico() -> dict:
    """Carrega o inventário do cache de forma segura. Ignora caches de versão antiga ou com métricas."""
    with _cache_lock:
        if not CACHE_FILE.exists():
            return None
            
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Verifica se é a versão 2 do schema
            if data.get("schema_version") != 2:
                return None
                
            # Validação anti-métricas: se encontrar campos dinâmicos, o cache é inválido
            # No v2, o cache é o próprio contrato.
            if "dados" in data: 
                # Este é o formato v1, rejeita.
                return None
                
            # Verifica se tem métricas persistidas acidentalmente na CPU ou GPU
            cpu = data.get("cpu", {})
            if "uso_percentual" in cpu or "frequencia_atual_mhz" in cpu:
                logger.warning("Cache rejeitado: contém métricas dinâmicas de CPU.")
                return None
                
            gpus = data.get("gpus", [])
            for g in gpus:
                if "uso_percentual" in g or "temperatura_c" in g or "vram_usada_mb" in g:
                    logger.warning("Cache rejeitado: contém métricas dinâmicas de GPU.")
                    return None
                    
            return data
        except Exception as e:
            logger.warning(f"Falha ao carregar cache de hardware: {e}")
            return None

def salvar_cache_estatico(inventario: dict) -> bool:
    """Salva o inventário atomicamente. Impede salvar se contiver métricas."""
    if inventario.get("schema_version") != 2:
        return False
        
    cpu = inventario.get("cpu", {})
    if "uso_percentual" in cpu or "frequencia_atual_mhz" in cpu:
        raise ValueError("Tentativa de salvar métricas dinâmicas no cache (CPU)")
        
    for g in inventario.get("gpus", []):
        if "uso_percentual" in g or "temperatura_c" in g or "vram_usada_mb" in g:
             raise ValueError("Tentativa de salvar métricas dinâmicas no cache (GPU)")

    with _cache_lock:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            temp_file = str(CACHE_FILE) + ".tmp"
            
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(inventario, f, ensure_ascii=False, indent=2)
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
