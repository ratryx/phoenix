import subprocess
import pytest
from pathlib import Path

def test_no_personal_paths_in_repo():
    # Only check files tracked by git
    try:
        tracked_files_raw = subprocess.check_output(
            ["git", "ls-files"], 
            stderr=subprocess.STDOUT,
            text=True
        )
    except subprocess.CalledProcessError as e:
        pytest.skip("Not a git repository or git not installed")
        
    files = [f.strip() for f in tracked_files_raw.splitlines() if f.strip()]
    
    # Exclude this very test file from the check to prevent self-triggering
    # if we define the forbidden strings explicitly here.
    current_file = Path(__file__).name
    
    import re
    
    # We construct forbidden patterns dynamically
    c_users_pat = re.compile(r"C:[/\\]+Users[/\\]+", re.IGNORECASE)
    thiago_pat = re.compile(r"Thiago", re.IGNORECASE)
    phoenix_abs_pat = re.compile(r"[A-Za-z]:[/\\]+.*phoenix-optimizer|/[^ ]+phoenix-optimizer", re.IGNORECASE)
    
    forbidden_scripts = ["refactor.py", "refactor2.py", "fix_whitespace.py"]
    
    violations = []
    
    for file_path in files:
        if file_path == current_file or file_path == "tests/" + current_file or current_file in file_path:
            continue
            
        path = Path(file_path)
        if not path.is_file():
            continue
            
        try:
            content = path.read_text(encoding="utf-8")
            
            if c_users_pat.search(content):
                violations.append(f"File {file_path} contains forbidden term 'C:\\Users\\'")
            if thiago_pat.search(content):
                violations.append(f"File {file_path} contains forbidden term 'Thiago'")
            if phoenix_abs_pat.search(content):
                violations.append(f"File {file_path} contains forbidden absolute path for 'phoenix-optimizer'")
                
            for script in forbidden_scripts:
                if script in content:
                    violations.append(f"File {file_path} contains forbidden script name '{script}'")
                    
        except UnicodeDecodeError:
            pass # ignore binary files
            
    assert not violations, "Found personal paths or temporary scripts in tracked files:\n" + "\n".join(violations)
