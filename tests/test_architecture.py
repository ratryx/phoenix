import ast
import os
from pathlib import Path

def test_no_subprocess_outside_windows_command():
    """
    Testa se nenhum arquivo em modules/ chama subprocess.run ou subprocess.Popen,
    exceto modules/core/windows_command.py.
    """
    project_root = Path(__file__).resolve().parent.parent
    modules_dir = project_root / "modules"
    
    # Arquivos permitidos a usar subprocess
    allowed_files = [
        modules_dir / "core" / "windows_command.py"
    ]
    
    violations = []
    
    for filepath in modules_dir.rglob("*.py"):
        if filepath in allowed_files:
            continue
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            continue
            
        try:
            tree = ast.parse(content, filename=str(filepath))
        except SyntaxError:
            continue
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                        if node.func.attr in ("run", "Popen"):
                            violations.append(f"{filepath.relative_to(project_root)}: {node.lineno}")
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ("run", "Popen"):
                        # Verifica se foi importado de subprocess (heuristica basica)
                        if "subprocess" in content:
                            violations.append(f"{filepath.relative_to(project_root)}: {node.lineno}")
                            
    assert not violations, f"Encontrado uso de subprocess fora do core: {violations}"
