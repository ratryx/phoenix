# Quickstart Validation Guide: Windows GUI Validation

This guide outlines the steps to build, run, and manually validate the Phoenix Optimizer on a native Windows environment, verifying that the console attachment and GUI logic operate correctly.

## Prerequisites

* **Operating System**: Windows 10 or Windows 11.
* **Environment**: Python 3.12+ with `pip` installed.
* **Dependencies**: Install required packages using:
  ```powershell
  pip install -r requirements.txt
  pip install pywin32  # Recommended helper if needed, but we use ctypes for kernel32.AttachConsole
  ```

---

## Build Instructions

To generate the single executable without a persistent console window, run PyInstaller using the modified spec file:

```powershell
pyinstaller phoenix.spec
```

The output executable will be created at:
`dist\PhoenixOptimizer.exe`

---

## Validation Scenarios

Follow these scenarios to verify successful implementation.

### Scenario 1: GUI Double-Click Execution (No Console Window)
1. Navigate to the `dist\` folder in Windows Explorer.
2. Double-click `PhoenixOptimizer.exe`.
3. **Expected Outcome**:
   * The Phoenix Optimizer GUI window should launch successfully.
   * **No black Command Prompt / terminal window** should appear behind the GUI or on the taskbar.

### Scenario 2: CLI execution from Terminal (AttachConsole)
1. Open a new Command Prompt (`cmd.exe`) or PowerShell window.
2. Navigate to the project root or the `dist\` folder.
3. Run the executable with the CLI instruction:
   ```powershell
   .\dist\PhoenixOptimizer.exe
   ```
4. **Expected Outcome**:
   * The executable should attach to the existing shell session.
   * The initial Mode Selection screen and subsequent CLI interactive menus should print directly in the active shell.
   * Entering options should work interactively.

### Scenario 3: GUI Navigation and Drag Validation
1. Launch the application in GUI mode.
2. Click and hold the top-most title bar area of the window, then move the mouse.
   * **Expected Outcome**: The frameless window moves smoothly following the mouse.
3. Click through each item in the side navigation menu:
   * Home, Hardware, Diagnóstico, Limpeza, Otimização, Serviços, Histórico, Configurações (8 pages total).
   * **Expected Outcome**: Each page navigates successfully without script errors or rendering failures.

### Scenario 4: Python-JS Communication
1. In GUI mode, navigate to the **Hardware** page.
2. **Expected Outcome**:
   * The hardware details (CPU, RAM, GPU) should load and show real data. This proves the Python → JS bridge is successfully fetching data from the Windows host via `psutil`/`modules.hardware` and rendering it.
3. Click the minimize (`_`) and close (`X`) buttons on the top-right custom window controls.
   * **Expected Outcome**: Minimizing hides the window; closing exits the application completely.
