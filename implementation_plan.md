# Phoenix Optimizer Fixes Plan

## Goal
To implement two focused fixes to the Phoenix Optimizer:
1. **Scope A - Restore Point Hardening**: Fix the restore point flow by adding real preflight checks, updating the risk modal, and ensuring truthful logs.
2. **Scope B - Routine Progress Overlay Redesign**: Redesign the routine-complete overlay to a product-grade UI, adding a global progress bar, a stepper, summary metrics, and a polished activity list while preserving the dark Phoenix visual language.

## User Review Required
> [!IMPORTANT]
> The plan outlines specific UI structural changes and new PowerShell preflight checks. Please review the new actions in the risk modal and the structural changes proposed for the overlay. 

## Open Questions
- For opening System Protection, is `sysdm.cpl ,4` acceptable, or do you prefer `SystemPropertiesProtection.exe`? Both do exactly the same thing. (I will use `SystemPropertiesProtection.exe` by default).

## Proposed Changes

---

### Restore Point Hardening

#### [MODIFY] `modules/otimizacao.py`
- Enhance `criar_ponto_restauracao` with real preflight checks:
  - Verify Windows services (`VSS` and `swprv`).
  - Verify System Protection status via registry or `Get-ComputerRestorePoint`.
- Add explicit logging for the preflight check.
- Map failures to specific codes (e.g. `SERVICES_DISABLED`, `RESTORE_DISABLED`) without showing a success message on failure.

#### [MODIFY] `modules/gui/api.py`
- Add a new bridge method `abrir_protecao_sistema` that runs `SystemPropertiesProtection.exe`.

#### [MODIFY] `gui/js/operations/restore-point.js`
- Create a new function `exibirModalRiscoRestore` to replace `confirmarComModalLegado`.
- Handle the specific error codes returned from the backend.
- Wire up the 4 actions: "Open System Protection" (calls bridge), "Retry" (loops back), "Continue without protection", and "Cancel".

#### [MODIFY] `gui/index.html`
- Add the HTML structure for `#modal-risco-restore` containing the title, exact reason, impact explanation, and the 4 new buttons.

---

### Routine Progress Overlay Redesign

#### [MODIFY] `gui/index.html`
- Completely redesign the `#overlay-processando` container.
- Add a hierarchy: strong title, short subtitle, current phase label (e.g., 2/5).
- Add a compact stepper for phases (e.g., Diagnóstico, Limpeza, Otimizações, Relatório).
- Add live summary metrics containers (removed files, freed space).
- Add a recent activity list container for polished status badges.

#### [MODIFY] `gui/style.css`
- Add specific CSS rules for the new overlay elements (stepper, activity list, phase labels, summary metrics).
- Ensure the design follows the existing dark Phoenix visual language.

#### [MODIFY] `gui/js/ui/feedback.js`
- Update `mostrarOverlay`, `atualizarOverlay`, and `esconderOverlay` to control the new overlay elements.
- Avoid showing "0/0 items" during early preparation.
- Implement logic to map progress messages to the compact stepper phases and update the recent activity list dynamically based on the incoming details.

#### [MODIFY] `tests/js/test_frontend_core.js` (and Python tests if applicable)
- Add/update JS tests for the new restore-point preflight/result contracts and for the overlay state transitions.

## Verification Plan

### Automated Tests
- Run `npm test` or `node tests/js/test_frontend_core.js` to ensure the new restore point flow and modal logic pass.
- Run `pytest` for the `otimizacao.py` tests to ensure the preflight checks and error mapping work correctly.

### Manual Verification
- Trigger the routine complete flow.
- Verify the new overlay UI looks product-grade and updates properly.
- Temporarily disable System Protection and trigger the flow to test the preflight check, the new risk modal, and its buttons (Retry, Open System Protection, etc.).
