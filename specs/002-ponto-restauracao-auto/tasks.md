# Tasks: Ponto de Restauração Automático

**Input**: Design documents from `/specs/002-ponto-restauracao-auto/`

**Prerequisites**: [plan.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/002-ponto-restauracao-auto/plan.md) (required), [spec.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/002-ponto-restauracao-auto/spec.md) (required), [research.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/002-ponto-restauracao-auto/research.md), [data-model.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/002-ponto-restauracao-auto/data-model.md), [restoration-contract.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/002-ponto-restauracao-auto/contracts/restoration-contract.md)

**Tests**: Manual validation scenarios (as documented in `quickstart.md`).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify the context environment setup.

- [x] T001 Verify project structure in [specs/002-ponto-restauracao-auto/](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/002-ponto-restauracao-auto/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**[AVISO] CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Implement core restore point cmdlet call in [modules/otimizacao.py](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/modules/otimizacao.py)
- [x] T003 Implement error parsing and classification in [modules/otimizacao.py](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/modules/otimizacao.py)
- [x] T004 Expose API wrapper for restore point creation in [modules/gui_app.py](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/modules/gui_app.py)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Criação e Confirmação do Ponto de Restauração (Priority: P1)  MVP

**Goal**: Automatically trigger system restore point creation, show progress, and request confirmation before applying optimizations in CLI and GUI.

**Independent Test**: Trigger optimizations in CLI/GUI with admin rights, see the progress status/spinner, verify successful creation message, and confirm whether to proceed.

- [x] T005 [US1] Integrate restore point flow with spinner in [modules/cli_app.py](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/modules/cli_app.py)
- [x] T006 [P] [US1] Add custom modal container HTML structure in [gui/index.html](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/gui/index.html)
- [x] T007 [P] [US1] Implement custom modal CSS styles and animations in [gui/style.css](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/gui/style.css)
- [x] T008 [US1] Add Javascript controller for modal status and actions in [gui/app.js](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/gui/app.js)
- [x] T009 [US1] Create confirmed optimization execution bridges in [modules/gui_app.py](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/modules/gui_app.py)

**Checkpoint**: User Story 1 should be fully functional and testable independently in both CLI and GUI.

---

## Phase 4: User Story 2 - Tratamento de Falha na Criação (Priority: P2)

**Goal**: Catch system restore point failures (e.g. limit reached, disabled), show warning messages, and allow users to continue anyway or cancel.

**Independent Test**: Simulate restore point creation failure, verify error warning is displayed, and check that choosing "Continue" applies optimizations while "Cancel" aborts safely.

### Implementation for User Story 2

- [x] T010 [US2] Handle creation failure prompts in [modules/cli_app.py](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/modules/cli_app.py)
- [x] T011 [US2] Handle creation failure states in [gui/app.js](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/gui/app.js)

**Checkpoint**: Both user stories are complete and handle failure flows appropriately.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, logging compliance, and end-to-end validation.

- [x] T012 Verify logging outputs location in [modules/logs.py](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/modules/logs.py)
- [x] T013 Run validation scenarios from [quickstart.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/002-ponto-restauracao-auto/quickstart.md) and document results in `walkthrough.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup - blocks all User Stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion.
- **User Story 2 (Phase 4)**: Depends on Phase 2 completion (can run in parallel with Phase 3 UI work, but integrates after US1).
- **Polish (Phase 5)**: Depends on all user story tasks completion.

### Parallel Opportunities

- HTML [T006] and CSS [T007] designs can run in parallel.
- Foundational backend [T002-T004] and frontend structure [T006-T007] can run in parallel.
