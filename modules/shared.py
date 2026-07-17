import os, sys
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

def obter_pasta_base(cliente: str = None) -> Path:
    if IS_PORTABLE:
        base = obter_pasta_exe() / 'dados'
        if cliente:
            # Sanitizar nome do cliente para nome de pasta seguro
            nome_seguro = "".join(
                c for c in cliente if c.isalnum() or c in ' -_'
            ).strip().replace(' ', '-').lower()
            return base / 'clientes' / nome_seguro
        return base
    
    if sys.platform == "win32":
        return Path(os.environ.get("PROGRAMDATA", Path.home())) / "PhoenixOptimizer"
    elif getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent

# Cliente ativo na sessão atual (setado pelo launcher)
CLIENTE_ATIVO = None

def definir_cliente_ativo(nome: str):
    global CLIENTE_ATIVO, CACHE_DIR
    CLIENTE_ATIVO = nome
    CACHE_DIR = obter_pasta_base(nome) / "cache"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def obter_pasta_logs_atual() -> Path:
    pasta = obter_pasta_base(CLIENTE_ATIVO) / "logs"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta

def listar_clientes_portable() -> list:
    """Lista todos os clientes salvos no pen drive."""
    import json
    from datetime import datetime
    
    pasta_clientes = obter_pasta_exe() / 'dados' / 'clientes'
    if not pasta_clientes.exists():
        return []
    
    clientes = []
    for pasta in sorted(pasta_clientes.iterdir()):
        if not pasta.is_dir():
            continue
        
        # Tentar ler metadados
        meta_file = pasta / 'meta.json'
        nome_display = pasta.name.replace('-', ' ').title()
        ultimo_atendimento = None
        total_atendimentos = 0
        
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                nome_display = meta.get('nome_display', nome_display)
                ultimo_atendimento = meta.get('ultimo_atendimento')
                total_atendimentos = meta.get('total_atendimentos', 0)
            except Exception:
                pass
        
        # Contar atendimentos pelos logs
        pasta_logs = pasta / 'logs'
        if pasta_logs.exists():
            total_atendimentos = len(list(pasta_logs.glob('*_antes.json')))
        
        clientes.append({
            'id': pasta.name,
            'nome': nome_display,
            'ultimo_atendimento': ultimo_atendimento,
            'total_atendimentos': total_atendimentos,
            'pasta': str(pasta)
        })
    
    return sorted(clientes, 
                  key=lambda x: x['ultimo_atendimento'] or '', 
                  reverse=True)

def remover_cliente_portable(id_cliente: str) -> bool:
    """Remove a pasta do cliente do pen drive."""
    import shutil
    pasta = obter_pasta_exe() / 'dados' / 'clientes' / id_cliente
    if pasta.exists() and pasta.is_dir():
        try:
            shutil.rmtree(pasta, ignore_errors=True)
            return True
        except Exception:
            pass
    return False

def salvar_meta_cliente(nome: str):
    """Salva/atualiza os metadados do cliente ativo."""
    import json
    from datetime import datetime
    
    pasta = obter_pasta_base(nome)
    pasta.mkdir(parents=True, exist_ok=True)
    meta_file = pasta / 'meta.json'
    
    meta = {}
    if meta_file.exists():
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception:
            pass
    
    meta['nome_display'] = nome
    meta['ultimo_atendimento'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

CACHE_DIR = obter_pasta_base() / "cache"
