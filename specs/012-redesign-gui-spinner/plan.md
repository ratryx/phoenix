# Implementation Plan: Redesign GUI + Correção Definitiva do Spinner

**Branch**: `012-redesign-gui-spinner` | **Date**: 2026-07-08 | **Spec**: [specs/012-redesign-gui-spinner/spec.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/012-redesign-gui-spinner/spec.md)

**Input**: Feature specification from `specs/012-redesign-gui-spinner/spec.md`

## Summary

Refatorar a API Python da GUI (`gui_app.py`) para que **nenhuma operação pesada** bloqueie a thread principal do `pywebview`, adotando estritamente o padrão assíncrono com `job_id`. Implementar também um redesign da interface visual com uma Sidebar e Slots para navegação fluida em abas (preparando para HWMonitor e CPU-Z), corrigindo de forma definitiva o congelamento visual do spinner durante carregamentos.

## Technical Context

**Language/Version**: Python 3.12+ (Backend), HTML/CSS/JS (Frontend)

**Primary Dependencies**: `pywebview`

**Storage**: Arquivos de cache e logs em `%PROGRAMDATA%\PhoenixOptimizer\`

**Testing**: Validação manual no Windows (Princípio VII da Constituição)

**Target Platform**: Windows (Desktop App)

**Project Type**: Desktop App com arquitetura GUI em tecnologias Web

**Performance Goals**: Animações de spinner fluídas a 60 fps, interatividade contínua na janela (arrastar/minimizar) sem congelamentos.

**Constraints**: Backend Python restrito ao motor WebView2. Polling JS deve ser feito em `setInterval` a cada 500ms.

**Scale/Scope**: Todas as funções do `gui_app.py` devem obedecer a arquitetura assíncrona, além de uma nova estrutura HTML.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Princípio I (Cirúrgico e Não Destrutivo)**: O redesign isola a estrutura de navegação em slots dinâmicos, preservando a lógica central do HTML e dos retornos das APIs. Refatorações na API Python são adições do padrão `_iniciar_job`, o que minimiza impactos destrutivos nas chamadas do motor central (modules). PASS.
- **Princípio IV (Isolamento de Logs)**: Sem alterações na gravação de logs (preserva-se uso do ProgramData). PASS.
- **Princípio VI (Dual-Interface)**: Nenhuma alteração afetará a CLI. A interface gráfica continuará utilizando a mesma lógica de negócios (modules), apenas o wrapper da API pywebview será adaptado. PASS.
- **Princípio VII (Validação de Empacotamento)**: Exige teste final interativo na janela para validar o spinner e arraste. PASS.

## Project Structure

### Documentation (this feature)

```text
specs/012-redesign-gui-spinner/
├── plan.md              # This file
├── research.md          # Output of Phase 0
├── data-model.md        # Output of Phase 1
├── quickstart.md        # Output of Phase 1
├── contracts/           # Output of Phase 1
└── tasks.md             # To be generated in Phase 2
```

### Source Code (repository root)

```text
modules/
└── gui_app.py           # Backend endpoints a serem convertidos para job_id

gui/
├── index.html           # Novo layout base (Sidebar + Main Content)
├── css/
│   └── style.css        # Refinamento visual, design da Sidebar
└── js/
    └── main.js          # Implementação de polling JS nativo para os job_ids
```

**Structure Decision**: Option 1 (Single Project Desktop App). Modificações exclusivas em `gui_app.py` e arquivos estáticos localizados em `gui/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*Sem violações aos princípios da Constituição.*
