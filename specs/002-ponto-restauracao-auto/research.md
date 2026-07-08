# Research: Ponto de Restauração Automático

This document details the technical research, decisions, and options evaluated for executing System Restore points natively on Windows 10/11 using Python.

## Technical Decisions

### 1. Command Invocation Method
*   **Decision**: Invoke PowerShell's native cmdlet `Checkpoint-Computer` via the Python `subprocess` module.
*   **Command**: `powershell -ExecutionPolicy Bypass -Command "Checkpoint-Computer -Description 'Phoenix Optimizer - Pré-Otimização' -RestorePointType 'MODIFY_SETTINGS'"`
*   **Rationale**: 
    - `Checkpoint-Computer` is standard, robust, and supported natively on all desktop editions of Windows 10 and 11.
    - Using `-ExecutionPolicy Bypass` ensures the execution policy of the local system does not block our execution.
*   **Alternatives Considered**:
    - **WMI/CIM Query directly in Python** (e.g. using `wmi` or `pywin32` package): Rejected to avoid adding complex external binary dependencies. Relying on PowerShell is cleaner and has 100% native platform compatibility without setup.
    - **Command Prompt `wmic.exe`**: Rejected because `wmic shadowcopy` and related features are deprecated or removed in newer Windows 11 updates.

### 2. Frequency Limit Bypass / Graceful Recovery
*   **Decision**: Catch PowerShell errors, parsing the stderr output for code `0x80042316` (or any non-zero exit code of `Checkpoint-Computer`), and offer an interactive prompt to the user to bypass or abort.
*   **Rationale**:
    - By default, Windows limits System Restore point creation to once per 24 hours to prevent disk space exhaustion.
    - If a restore point was recently created (e.g. in the last 24 hours), `Checkpoint-Computer` will fail with an error.
    - We must allow the user to proceed anyway ("Continuar mesmo assim") or cancel ("Cancelar"), complying with functional requirements **FR-004** and **FR-005**.
*   **Alternatives Considered**:
    - **Registry Tweak (`SystemRestorePointCreationFrequency`)**: Windows has a registry key `HKLM:\Software\Microsoft\Windows NT\CurrentVersion\SystemRestore\SystemRestorePointCreationFrequency` which can be set to `0` to remove the 24-hour limit. However, editing HKLM registry keys is highly invasive. We should only do this if required, but letting the user skip the restore point check is safer, less intrusive, and respects Principle I (Cirúrgico e Não Destrutivo).

### 3. Execution UI/CLI Integration & Asynchronous Operation
*   **Decision**: 
    - **CLI**: Use `console.status("[bold yellow]Criando ponto de restauração do sistema... Isso pode levar até um minuto.")` from `rich` to render an active, animated spinner during the blocking subprocess call.
    - **GUI**: Since `pywebview` runs the Python API methods in a background worker thread, a blocking `subprocess.run` will not freeze the JS renderer thread. However, we must notify the frontend to show an overlay with a loading spinner while the checkpoint is running.
    - **Interactive Modals**: The Python backend will prompt for confirmation or error bypass.
        - CLI: Use `Confirm.ask` from `rich`.
        - GUI: We can invoke `window.confirm` via JS or a custom HTML modal on the frontend before/after execution. Using `window.confirm` via pywebview's `window.evaluate_js` or a backend-driven modal flow is very clean.
*   **Rationale**:
    - Ensures visual feedback during the 10-60 second execution time, fulfilling **FR-002**.
