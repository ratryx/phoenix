# Tasks: Redesign GUI + Correção Definitiva do Spinner

**Input**: Design documents from `/specs/012-redesign-gui-spinner/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Verify project structure and layout for GUI elements in `gui/index.html` and `modules/gui_app.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The backend API must be asynchronous before frontend polling is implemented.

- [ ] T002 Refatorar `listar_inicializacao()` para retornar `job_id` via `_iniciar_job()` em `modules/gui_app.py`
- [ ] T003 Refatorar `listar_servicos()` para retornar `job_id` via `_iniciar_job()` em `modules/gui_app.py`
- [ ] T004 Refatorar `obter_historico()` para retornar `job_id` via `_iniciar_job()` em `modules/gui_app.py`
- [ ] T005 Refatorar `listar_backups_rollback()` para retornar `job_id` via `_iniciar_job()` em `modules/gui_app.py`

**Checkpoint**: Foundation ready - backend agora é 100% assíncrono para operações pesadas.

---

## Phase 3: User Story 1 - Interface Responsiva durante Operações Pesadas (Priority: P1) 🎯 MVP

**Goal**: O técnico clica para executar operações demoradas e o spinner gira fluidamente sem travar a thread principal, mantendo a janela arrastável.

**Independent Test**: Clicar em "Rotina Completa" e mover a janela sem interrupções (60fps) durante todo o processo.

### Implementation for User Story 1

- [ ] T006 [P] [US1] Criar função utilitária `awaitJob(jobId)` com `setInterval` (polling) em `gui/js/main.js`
- [ ] T007 [P] [US1] Otimizar CSS do Spinner (`gui/css/style.css`) para garantir uso de transformações GPU (evitar reflow)
- [ ] T008 [US1] Modificar chamadas JS de Serviços e Inicialização em `gui/js/main.js` para consumir `awaitJob` e exibir spinner
- [ ] T009 [US1] Modificar chamadas JS de Histórico e Backups em `gui/js/main.js` para consumir `awaitJob` e exibir spinner

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Nova Estrutura de Navegação (Sidebar e Abas) (Priority: P2)

**Goal**: Criar um layout com Sidebar lateral e "Slots" (abas dinâmicas) no conteúdo principal, preparando o app para futuras expansões.

**Independent Test**: Clicar em "Logs" na Sidebar e ver a transição imediata para o respectivo slot na área central.

### Implementation for User Story 2

- [ ] T010 [P] [US2] Criar Sidebar (nav) e div `main-content` no layout de `gui/index.html`
- [ ] T011 [P] [US2] Transferir conteúdo existente (Dashboard, Logs, Otimizações) para as divs (`view-slot`) correspondentes em `gui/index.html`
- [ ] T012 [P] [US2] Implementar estilos para Sidebar e views ativas (`display: block/none`) em `gui/css/style.css`
- [ ] T013 [US2] Adicionar lógica JavaScript em `gui/js/main.js` para mapear os botões da Sidebar e alternar as abas visíveis instantaneamente

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T014 Run quickstart.md validation to ensure 60fps spinner and smooth UI behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independently testable.

### Parallel Opportunities

- Todos os refactors de `gui_app.py` na Phase 2 podem ser feitos em paralelo (T002-T005)
- Edições de CSS (T007, T012) e JS base (T006) podem ocorrer de forma assíncrona
