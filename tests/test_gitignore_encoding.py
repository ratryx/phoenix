import os

def test_gitignore_no_nul_bytes():
    """Confirma que o .gitignore não contém bytes NUL causados por redirects do powershell (UTF-16 LE)."""
    gitignore_path = os.path.join(os.path.dirname(__file__), '..', '.gitignore')
    if not os.path.exists(gitignore_path):
        return

    with open(gitignore_path, 'rb') as f:
        content = f.read()

    assert b'\x00' not in content, "O arquivo .gitignore contem bytes NUL. Por favor, ressalve-o como UTF-8 sem BOM."
