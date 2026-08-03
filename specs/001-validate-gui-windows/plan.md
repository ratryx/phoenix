# Implementation Plan: Windows GUI Validation

**Branch**: `001-validate-gui-windows` | **Date**: 2026-06-24 | **Spec**: [spec.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/001-validate-gui-windows/spec.md)

**Input**: Feature specification from `specs/001-validate-gui-windows/spec.md`

## Summary

This feature resolves a critical platform gap: validating the `pywebview`-based GUI on native Windows, ensuring both CLI and GUI modes work properly in a single compiled executable. 
To avoid a persistent black console window when running in GUI mode, the application will be compiled using PyInstaller's `--noconsole` flag. To preserve interactive CLI output and inputs when run from terminal, `launcher.py` will dynamically attach to the calling shell using the Windows API `AttachConsole` via `ctypes`. If no terminal parent process is detected (i.e. double-clicked from file manager), the console attachment fails and the app bypasses the CLI selection menu to start the GUI directly.

## Technical Context

* **Language/Version**: Python 3.12
* **Primary Dependencies**: `pywebview`, `psutil`, `rich`, `pyfiglet`, `ctypes` (standard library)
* **Storage**: JSON/TXT logs under `%PROGRAMDATA%\PhoenixOptimizer\logs` (no database)
* **Testing**: Manual verification on native Windows 10/11 using a detailed testing checklist
* **Target Platform**: Windows 10 & Windows 11
* **Project Type**: Desktop application (dual CLI/GUI interface)
* **Performance Goals**: Bidirectional GUI bridge response time < 50ms
* **Constraints**: 0 visible console windows on GUI double-click launch; attach to parent console on CLI terminal launch

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check/Status | Rationale |
| :--- | :--- | :--- |
| **Principle I: Cirúrgico e Não Destrutivo** | [OK] Pass | The changes are strictly confined to `launcher.py` (for console attachment) and `phoenix.spec` (packaging config). |
| **Principle VI: Dual-Interface CLI/GUI** | [OK] Pass | The design ensures both CLI and GUI modes remain fully operational and share the same code logic. |
| **Principle VII: Validação de Empacotamento** | [OK] Pass | We have defined a strict Windows validation checklist in [quickstart.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/001-validate-gui-windows/quickstart.md) to test the built executable on native Windows. |

## Project Structure

### Documentation (this feature)

```text
specs/001-validate-gui-windows/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Console attachment findings (ctypes)
├── data-model.md        # Execution state machine
├── quickstart.md        # Verification scenarios
├── contracts/
│   └── gui-bridge-contract.md  # JS <-> Python API contract
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code

```text
launcher.py               # Main entry point (incorporates AttachConsole logic)
phoenix.spec              # PyInstaller build specification (console=False)
modules/
└── gui_app.py            # GUI backend handler
```

**Structure Decision**: Single project structure is preserved. We make localized edits to the root files `launcher.py` and `phoenix.spec`.

## Complexity Tracking

> *No principles were violated; complexity tracking table is empty.*

---

## Verification Plan

We will perform automated static analysis and extensive manual validation.

### Automated Verification
* Verify syntax and compile sanity of python changes using:
  ```powershell
  python -m py_compile launcher.py
  ```

### Manual Verification
Refer to [quickstart.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/001-validate-gui-windows/quickstart.md) for step-by-step validation steps:
1. Compile using PyInstaller.
2. Launch via double-click (validate GUI works, no command prompt window pops up).
3. Launch from CLI terminal (validate attached console prints rich panels and accepts interactive inputs).
4. Verify JS↔Python bridge functions by loading hardware details and using window close controls.
5. Verify 8-page navigation.
