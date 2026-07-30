import pytest
import shutil
from pathlib import Path

@pytest.fixture(autouse=True)
def _global_test_isolation(monkeypatch, tmp_path):
    """
    Global isolation for all tests.
    Ensures that no test writes to the real repository 'dados/clientes/' directory,
    and that global state mutations in modules.shared are rolled back automatically.
    """
    import modules.shared as ms
    
    # Snapshot of global states
    orig_is_portable = ms.IS_PORTABLE
    orig_cliente_ativo_id = getattr(ms, 'CLIENTE_ATIVO_ID', None)
    orig_cliente_ativo_nome = getattr(ms, 'CLIENTE_ATIVO_NOME', None)
    orig_cache_dir = getattr(ms, 'CACHE_DIR', None)
    
    # Redirect base folder to tmp_path
    fake_exe_dir = tmp_path / "fake_repo_root"
    fake_exe_dir.mkdir()
    
    # Safely mock obter_pasta_exe for ALL tests, enforcing isolation
    monkeypatch.setattr(ms, "obter_pasta_exe", lambda: fake_exe_dir)
    
    # Keep track of the real dados/clientes path for the regression check
    repo_root = Path(__file__).resolve().parent.parent
    dados_clientes = repo_root / "dados" / "clientes"
    
    # We shouldn't delete existing data if it's there, but we snapshot it
    def get_paths():
        if not dados_clientes.exists():
            return set()
        return set(p.relative_to(dados_clientes) for p in dados_clientes.rglob("*"))
        
    before_paths = get_paths()
    
    yield  # Run the test
    
    # Restore globals explicitly to handle direct assignments that monkeypatch misses
    ms.IS_PORTABLE = orig_is_portable
    ms.CLIENTE_ATIVO_ID = orig_cliente_ativo_id
    ms.CLIENTE_ATIVO_NOME = orig_cliente_ativo_nome
    ms.CACHE_DIR = orig_cache_dir
    
    after_paths = get_paths()
    new_paths = after_paths - before_paths
    
    # Regression safeguard: if a test created new children inside the repo, fail it
    if new_paths:
        pytest.fail(
            f"Regression: A test violated isolation and created {new_paths} inside the repository. "
            "Tests must use mock_portable or tmp_path."
        )
