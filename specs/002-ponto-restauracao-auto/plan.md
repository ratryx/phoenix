# Implementation Plan: Ponto de Restauração Automático

**Branch**: `002-ponto-restauracao-auto` | **Date**: 2026-06-25 | **Spec**: [spec.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/002-ponto-restauracao-auto/spec.md)

**Input**: Feature specification from `/specs/002-ponto-restauracao-auto/spec.md`

## Summary

Implement automatic Windows Restore Point creation via PowerShell's `Checkpoint-Computer` cmdlet before running any system optimization or modifying services. Show progress/status to the user. Require confirmation to proceed or bypass/cancel on failure. Shared core logic for both CLI and GUI.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: `pywebview`, `rich`, `psutil`, `subprocess`

**Storage**: Local files (logs under `%PROGRAMDATA%\PhoenixOptimizer\logs`)

**Testing**: Manual verification on Windows 10/11, custom Python scripts for unit checking

**Target Platform**: Windows 10/11

**Project Type**: desktop-app (CLI/GUI)

**Performance Goals**: N/A

**Constraints**:
- Requires Administrator privileges to run `Checkpoint-Computer`.
- Windows by default limits creation to one restore point per 24 hours. We must catch and handle this error gracefully (Code 0x80042316 or similar PowerShell errors) and offer the user options to "Continue anyway" or "Cancel".

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Cirúrgico e Não Destrutivo**: Pass. Changes are highly targeted and act as a safety net before optimizations.
- **Principle II: Ponto de Restauração Obrigatório**: Pass. The core goal of this feature is to enforce restore point creation.
- **Principle III: Controle de Serviços Fixos**: Pass. We do not modify or expand the list of services.
- **Principle IV: Isolamento de Logs**: Pass. Any logging generated will be stored in `%PROGRAMDATA%\PhoenixOptimizer\logs`.
- **Principle V: Transparência de Performance**: Pass. No FPS claims are added.
- **Principle VI: Dual-Interface CLI/GUI**: Pass. Core restoration logic will be central in `modules/otimizacao.py` or a dedicated module, then invoked identically by CLI and GUI.
- **Principle VII: Validação de Empacotamento**: Pass. No packaging changes are made, but verification will be performed on Windows.

## Project Structure

### Documentation (this feature)

```text
specs/002-ponto-restauracao-auto/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
gui/
├── app.js
├── index.html
└── style.css

modules/
├── cli_app.py
├── gui_app.py
├── otimizacao.py
└── logs.py

launcher.py
```

**Structure Decision**: Single project layout (Option 1/default). The core business logic resides in `modules/`, shared by CLI (`modules/cli_app.py`) and GUI (`modules/gui_app.py` and `gui/` frontend files).

## Complexity Tracking

> *No violations to justify.*

