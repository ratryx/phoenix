import ast
import os
from pathlib import Path

def check_python_file_for_subprocess(filepath, content, project_root):
    try:
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        return [f"{filepath.relative_to(project_root) if hasattr(filepath, 'relative_to') else filepath}: SyntaxError"]
        
    subprocess_aliases = {"subprocess"}
    os_aliases = {"os"}
    func_aliases = {
        "run": "run", "Popen": "Popen", "call": "call",
        "check_call": "check_call", "check_output": "check_output",
        "system": "system"
    }
    
    violations = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name == "subprocess":
                    if name.asname:
                        subprocess_aliases.add(name.asname)
                elif name.name == "os":
                    if name.asname:
                        os_aliases.add(name.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "subprocess":
                for name in node.names:
                    func_aliases[name.asname or name.name] = name.name
            elif node.module == "os":
                for name in node.names:
                    if name.name == "system":
                        func_aliases[name.asname or name.name] = "system"
                        
        elif isinstance(node, ast.Call):
            call_found = False
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id in subprocess_aliases and node.func.attr in ("run", "Popen", "call", "check_call", "check_output"):
                        call_found = True
                    elif node.func.value.id in os_aliases and node.func.attr == "system":
                        call_found = True
            elif isinstance(node.func, ast.Name):
                if node.func.id in func_aliases and func_aliases[node.func.id] in ("run", "Popen", "call", "check_call", "check_output", "system"):
                    call_found = True
                    
            if call_found:
                rel = filepath.relative_to(project_root) if hasattr(filepath, 'relative_to') else filepath
                violations.append(f"{rel}: {node.lineno}")
                
            # Check for shell=True
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    rel = filepath.relative_to(project_root) if hasattr(filepath, 'relative_to') else filepath
                    violations.append(f"{rel}: {node.lineno} (shell=True)")
                    
    return violations


def test_no_subprocess_outside_windows_command():
    """
    Testa se nenhum arquivo em modules/ ou launcher.py chama subprocess.run ou subprocess.Popen,
    exceto modules/core/windows_command.py. Resolve import aliases.
    """
    project_root = Path(__file__).resolve().parent.parent
    modules_dir = project_root / "modules"
    launcher_file = project_root / "launcher.py"
    
    allowed_files = [
        modules_dir / "core" / "windows_command.py"
    ]
    
    files_to_scan = list(modules_dir.rglob("*.py"))
    if launcher_file.exists():
        files_to_scan.append(launcher_file)
        
    violations = []

    for filepath in files_to_scan:
        if filepath in allowed_files:
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            violations.append(f"{filepath.relative_to(project_root)}: ReadError")
            continue
            
        file_violations = check_python_file_for_subprocess(filepath, content, project_root)
        violations.extend(file_violations)
                            
    assert not violations, f"Encontrado uso de subprocess fora do core: {violations}"


def test_architecture_self_test():
    malicious_code = [
        "import subprocess as sp\nsp.run(['ls'])",
        "from subprocess import Popen as launch\nlaunch(['ls'])",
        "import os as operating_system\noperating_system.system('ls')",
        "import subprocess\nsubprocess.run(['ls'], shell=True)"
    ]
    
    for code in malicious_code:
        violations = check_python_file_for_subprocess(Path("fake.py"), code, Path("."))
        assert violations, f"Did not catch: {code}"
