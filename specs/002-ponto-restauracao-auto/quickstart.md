# Quickstart Validation Guide: Ponto de Restauração Automático

This guide outlines the steps to run and manually validate the automatic Windows System Restore point creation in both the CLI and GUI modes of the Phoenix Optimizer.

## Prerequisites

*   **Operating System**: Windows 10 or Windows 11.
*   **Privileges**: The application must be launched with **Administrator privileges** (Run as Administrator) to allow PowerShell's `Checkpoint-Computer` cmdlet to run.
*   **Environment**: Python 3.12+ with dependencies installed:
    ```powershell
    pip install -r requirements.txt
    ```

---

## Validation Scenarios

Refer to [restoration-contract.md](file:///C:\MockUsers\Developer/Desktop/app-optimizer/specs/002-ponto-restauracao-auto/contracts/restoration-contract.md) and [data-model.md](file:///C:\MockUsers\Developer/Desktop/app-optimizer/specs/002-ponto-restauracao-auto/data-model.md) for background details on the contracts and states.

### Scenario 1: CLI Automatic Creation and Success Flow
1. Open PowerShell or CMD as **Administrator**.
2. Run the application in CLI mode:
   ```powershell
   python launcher.py
   ```
3. Enter option `1` (Otimização geral) or `2` (Otimização para jogos).
4. **Expected Outcome**:
   * A spinner status message should appear: `Criando ponto de restauração do sistema... Isso pode levar até um minuto.`
   * Once successfully created, a prompt must appear: `Ponto de restauração criado com sucesso! Deseja prosseguir com as otimizações? (y/n)`
   * If you choose `y`, the optimizations should run.
   * If you choose `n`, the operation aborts, no optimizations are executed, and you return to the main menu.

### Scenario 2: GUI Automatic Creation and Success Flow
1. Open PowerShell or CMD as **Administrator**.
2. Run the application in GUI mode:
   ```powershell
   python launcher.py --gui
   ```
3. Go to the **Otimização** section and click **Otimização Geral** or **Otimização para Jogos**.
4. **Expected Outcome**:
   * The overlay should show: `Criando ponto de restauração...`.
   * When successful, a custom modal dialog must appear stating: `Ponto de restauração criado com sucesso! Deseja prosseguir com as otimizações?`
   * Clicking **Sim/Confirmar** applies the optimizations.
   * Clicking **Não/Cancelar** aborts the operation safely, closing the modal.

### Scenario 3: Bypassing Creation Failures (Limit Exceeded / System Protection Disabled)
To simulate a failure:
*   *Option A*: Run Scenario 1 or 2 again within 24 hours of a successful restore point creation. (Windows limits restore points to once per 24 hours).
*   *Option B*: Disable System Protection on the C: drive (via `SystemPropertiesProtection` dialog) before running.
1. Run either CLI or GUI mode as **Administrator** under one of the failure conditions above.
2. Trigger any optimization.
3. **Expected Outcome**:
   * **CLI**: A warning appears detailing the error (e.g. daily limit reached or restore disabled), prompting: `A criação do ponto de restauração falhou (Motivo: <erro>). Deseja prosseguir com as otimizações mesmo assim? (y/n)`.
     * Choosing `y` proceeds with the optimizations.
     * Choosing `n` cancels the operation.
   * **GUI**: A beautiful warning modal appears with the failure message, presenting two buttons: **Continuar mesmo assim** and **Cancelar**.
     * Clicking **Continuar mesmo assim** applies the optimizations.
     * Clicking **Cancelar** aborts the operation safely.

### Scenario 4: Non-Admin Privileges Warning
1. Launch the application (CLI or GUI) **without** Administrator privileges (regular user).
2. Attempt to trigger any optimization.
3. **Expected Outcome**:
   * The program detects that it is running without Administrator privileges.
   * **CLI**: Prints a warning: `O Phoenix Optimizer requer privilégios de administrador para criar pontos de restauração e aplicar otimizações.` and aborts.
   * **GUI**: Shows a warning dialog indicating that Admin privileges are required, and cancels the action.
