# Research: Windows GUI Validation and Console Attachment

## Decisions

### 1. Windows Console Attachment Strategy
* **Decision**: We will use `ctypes` to invoke `AttachConsole(-1)` at the very beginning of `launcher.py`. If it returns a non-zero value (success), we will redirect Python's `sys.stdout`, `sys.stderr`, and `sys.stdin` to `CONOUT$` (for writing) and `CONIN$` (for reading). If it fails (returns 0, meaning the app was launched without a terminal parent process), we will automatically skip the CLI choice menu and start the GUI directly.
* **Rationale**: This provides a seamless user experience. Double-clicking the `.exe` launches the GUI immediately and without a black console window, while launching the `.exe` from CMD/PowerShell retains full interactive CLI functionality in the same console session.
* **Alternatives Considered**: 
  - *Separate executables*: Build `phoenix-cli.exe` and `phoenix-gui.exe`. Rejected because it creates build complexity and divides the entry points, whereas the prompt specified a single executable.
  - *AllocConsole*: Allocating a new console window if run from terminal. Rejected because it opens a new popup console instead of running inline in the user's active shell.

### 2. PyInstaller Packaging Configuration
* **Decision**: Set `console=False` in `phoenix.spec`.
* **Rationale**: This compiles the executable as a Windows GUI Subsystem application, ensuring Windows does not allocate/show a console window when the process starts.
* **Alternatives Considered**: Running a post-build script to hide the console window. Rejected because modifying `console=False` is native, cleaner, and standard.

---

## Technical Details & Code Snippets

### AttachConsole Implementation
```python
import sys
import ctypes

def setup_console():
    """
    Tenta anexar o processo ao console do processo pai (ex: CMD/PowerShell).
    Retorna True se anexado com sucesso, False caso contrário.
    """
    if sys.platform != "win32":
        return False
        
    ATTACH_PARENT_PROCESS = -1
    kernel32 = ctypes.windll.kernel32
    
    # Tenta anexar ao console pai
    if kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
        try:
            # Redireciona stdout e stderr para o console
            sys.stdout = open("CONOUT$", "w", encoding="utf-8")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8")
            # Redireciona stdin para leitura interativa
            sys.stdin = open("CONIN$", "r", encoding="utf-8")
            return True
        except Exception:
            return False
    return False
```

### Launcher integration
No `launcher.py`, na inicialização, chamamos `setup_console()`. Se retornar `False`, forçamos a execução direta do modo GUI (pulando a tela de escolha de modo que requer terminal).
