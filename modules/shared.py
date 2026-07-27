import os, sys, shutil, json, uuid
from datetime import datetime
from pathlib import Path
from rich.console import Console

console = Console()

def _detectar_modo_portable() -> bool:
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
    else:
        exe_dir = Path(__file__).resolve().parent.parent
    return (exe_dir / 'PORTABLE').exists()

IS_PORTABLE = _detectar_modo_portable()

def obter_pasta_exe() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def obter_pasta_clientes() -> Path:
    return obter_pasta_exe() / 'dados' / 'clientes'

def _validar_id_cliente(id_cliente: str) -> bool:
    if not id_cliente or not isinstance(id_cliente, str):
        return False
    if len(id_cliente) > 100:
        return False
    if any(c in id_cliente for c in ['/', '\\', '.', '\0']):
        return False
    reserved = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
    if id_cliente.upper() in reserved:
        return False
    return True

def _is_safe_dir(pasta: Path) -> bool:
    if not pasta.is_dir():
        return False
    if pasta.is_symlink():
        return False
    if hasattr(os.path, 'isjunction') and os.path.isjunction(str(pasta)):
        return False
    return True

def _write_json_atomic(filepath: Path, data: dict) -> bool:
    import tempfile
    try:
        fd, temp_path = tempfile.mkstemp(dir=filepath.parent, text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, filepath)
        return True
    except Exception:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return False

def criar_cliente_portable(nome: str) -> dict:
    import unicodedata
    import re
    nome = nome.strip() if nome else "Cliente Sem Nome"
    
    # Strip accents
    n_acc = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    # Keep only alphanumeric and spaces
    slug = "".join(c for c in n_acc if c.isalnum() or c == ' ')
    # Replace spaces with hyphens, reduce multiple hyphens
    slug = re.sub(r'\s+', '-', slug.strip()).lower()
    
    if not slug:
        slug = "cliente"
    slug = slug[:50]
    id_cliente = f"{slug}-{uuid.uuid4().hex[:8]}"
    
    pasta = obter_pasta_clientes() / id_cliente
    criada_agora = False
    if not pasta.exists():
        pasta.mkdir(parents=True, exist_ok=True)
        criada_agora = True
    
    meta_file = pasta / 'meta.json'
    meta = {
        'id': id_cliente,
        'nome_display': nome,
        'ultimo_atendimento': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'total_atendimentos': 0
    }
    if not _write_json_atomic(meta_file, meta):
        if criada_agora:
            try:
                pasta.rmdir()
            except Exception:
                pass
        return {"ok": False, "erro": "PERSISTENCE_WRITE_FAILED"}
        
    return meta

def obter_pasta_base(id_cliente: str = None) -> Path:
    if IS_PORTABLE:
        base = obter_pasta_exe() / 'dados'
        if id_cliente:
            if not _validar_id_cliente(id_cliente):
                raise ValueError("ID de cliente inválido")
            pasta = base / 'clientes' / id_cliente
            pasta_absoluta = pasta.resolve()
            raiz_absoluta = (base / 'clientes').resolve()
            if not str(pasta_absoluta).startswith(str(raiz_absoluta)) or pasta_absoluta == raiz_absoluta:
                raise ValueError("Path traversal detectado")
            return pasta
        return base
    
    if sys.platform == "win32":
        return Path(os.environ.get("PROGRAMDATA", Path.home())) / "PhoenixOptimizer"
    elif getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent

# Cliente ativo na sessão atual
CLIENTE_ATIVO_ID = None
CLIENTE_ATIVO_NOME = None

def definir_cliente_ativo(id_cliente: str, nome_cliente: str = ""):
    global CLIENTE_ATIVO_ID, CLIENTE_ATIVO_NOME, CACHE_DIR
    if IS_PORTABLE and id_cliente and not _validar_id_cliente(id_cliente):
        raise ValueError("ID de cliente inválido")
    CLIENTE_ATIVO_ID = id_cliente
    CLIENTE_ATIVO_NOME = nome_cliente
    CACHE_DIR = obter_pasta_base(id_cliente) / "cache"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def obter_pasta_logs_atual() -> Path:
    pasta = obter_pasta_base(CLIENTE_ATIVO_ID) / "logs"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta

def listar_clientes_portable() -> list:
    """Lista todos os clientes salvos no pen drive."""
    pasta_clientes = obter_pasta_clientes()
    if not pasta_clientes.exists():
        return []
    
    clientes = []
    for pasta in sorted(pasta_clientes.iterdir()):
        if not _is_safe_dir(pasta):
            continue
            
        id_pasta = pasta.name
        if id_pasta.startswith('.') or not _validar_id_cliente(id_pasta):
            continue
        
        meta_file = pasta / 'meta.json'
        nome_display = id_pasta.replace('-', ' ').title()
        ultimo_atendimento = None
        total_atendimentos = 0
        
        meta_id = id_pasta
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                leaked_id = meta.get('id')
                if leaked_id and leaked_id != id_pasta:
                    import logging
                    logging.warning(f"Metadata ID mismatch in client {id_pasta}. The directory name will remain the authoritative ID.")
                nome_display = meta.get('nome_display', nome_display)
                ultimo_atendimento = meta.get('ultimo_atendimento')
                total_atendimentos = meta.get('total_atendimentos', 0)
            except Exception:
                pass
        
        pasta_logs = pasta / 'logs'
        if pasta_logs.exists():
            total_atendimentos = len(list(pasta_logs.glob('*_antes.json')))
        
        clientes.append({
            'id': meta_id,
            'nome': nome_display,
            'ultimo_atendimento': ultimo_atendimento,
            'total_atendimentos': total_atendimentos
        })
    
    return sorted(clientes, 
                  key=lambda x: x['ultimo_atendimento'] or '', 
                  reverse=True)

def remover_cliente_portable(id_cliente: str) -> dict:
    """Remove a pasta do cliente do pen drive. Retorna dict estruturado."""
    if not IS_PORTABLE:
        return {"ok": False, "erro": "PORTABLE_MODE_REQUIRED"}
    if not _validar_id_cliente(id_cliente):
        return {"ok": False, "erro": "INVALID_CLIENT_ID"}
        
    pasta_clientes = obter_pasta_clientes()
    pasta = pasta_clientes / id_cliente
    
    try:
        pasta_absoluta = pasta.resolve()
        raiz_absoluta = pasta_clientes.resolve()
        if not str(pasta_absoluta).startswith(str(raiz_absoluta)) or pasta_absoluta == raiz_absoluta:
            return {"ok": False, "erro": "CLIENT_DELETE_FAILED"}
    except Exception:
        return {"ok": False, "erro": "CLIENT_DELETE_FAILED"}
        
    if not pasta.exists() or not _is_safe_dir(pasta):
        return {"ok": False, "erro": "CLIENT_NOT_FOUND"}
        
    try:
        shutil.rmtree(pasta)
        return {"ok": True}
    except PermissionError:
        return {"ok": False, "erro": "CLIENT_DELETE_FAILED_PERMISSION"}
    except Exception:
        return {"ok": False, "erro": "CLIENT_DELETE_FAILED"}

def salvar_meta_cliente(id_cliente: str, nome: str) -> dict:
    """Salva/atualiza os metadados do cliente ativo. Retorna o status da operação."""
    if not _validar_id_cliente(id_cliente):
        return {"ok": False, "erro": "INVALID_CLIENT_ID"}
        
    pasta = obter_pasta_base(id_cliente)
    pasta.mkdir(parents=True, exist_ok=True)
    meta_file = pasta / 'meta.json'
    
    meta = {}
    if meta_file.exists():
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception:
            pass
    
    meta['id'] = id_cliente
    meta['nome_display'] = nome
    meta['ultimo_atendimento'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    if not _write_json_atomic(meta_file, meta):
        return {"ok": False, "erro": "PERSISTENCE_WRITE_FAILED"}
    return {"ok": True}

CACHE_DIR = obter_pasta_base() / "cache"
