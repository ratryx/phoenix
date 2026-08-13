# Tasks

## Scope A: Restore Point Hardening
- `[x]` Update `modules/otimizacao.py` `criar_ponto_restauracao` with preflight checks and strict failure codes.
- `[x]` Add `abrir_protecao_sistema` bridge method in `modules/gui/api.py`.
- `[x]` Add `#modal-risco-restauracao` HTML in `gui/index.html`.
- `[x]` Update `gui/js/operations/restore-point.js` to parse new errors and manage the new risk modal.
- `[x]` Add Python tests for `otimizacao.py` restore point preflight.
- `[x]` Commit Scope A changes.

## Scope B: Routine Progress Overlay Redesign
- `[x]` Redesign `#overlay-processando` in `gui/index.html` with stepper, global progress, and activity list.
- `[x]` Add new CSS styles in `gui/style.css` for the redesigned overlay.
- `[x]` Update `gui/js/ui/feedback.js` to control new overlay elements.
- `[x]` Update JS tests for overlay state transitions.
- `[x]` Commit Scope B changes.
