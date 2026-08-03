---

description: "Task list for feature 010 and 011 implementation"
---

# Tasks: Diagnóstico de Status das Otimizações & Cache de Hardware (010 & 011)

**Input**: Design documents from `/specs/010-diagnostico-status-otimizacoes/` (including 011)

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Adicionar constantes de diretório `%PROGRAMDATA%\PhoenixOptimizer\cache` ao arquivo de configuração / `shared.py`
- [X] T002 Preparar `modules/gui_app.py` com dicionário global `_tarefas` e criar API `/api/tarefa/status` para suportar arquitetura `job_id`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**[AVISO] CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Implementar funções de leitura rápida WMI/psutil (para modelo CPU e RAM total) em `modules/hardware.py`
- [X] T004 Criar estrutura de dados (dicionário/lista) mapeando chaves de registro e serviços a serem verificados em `modules/otimizacao.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 4 (Priority: P1)  MVP

**Goal**: Verificar estado das otimizações ativas (US1) e Abertura instantânea com cache (US4)

**Independent Test**: Rodar o app; hardware deve carregar do cache instantaneamente. Status das otimizações deve refletir o estado real do Windows.

### Implementation for User Story 1 & 4

- [X] T005 [P] [US1] Implementar função `verificar_status_otimizacoes()` em `modules/otimizacao.py` usando `winreg` para leitura de registro
- [X] T006 [P] [US4] Implementar persistência e carregamento de JSON em `modules/hardware.py`
- [X] T007 [US1] Integrar menu de diagnóstico na CLI em `modules/cli_app.py` exibindo cores (verde/vermelho)
- [X] T008 [US4] Atualizar a inicialização do módulo de hardware na CLI para tentar ler o cache em `modules/cli_app.py`
- [X] T009 [US1] Expor rota de API `/api/otimizacoes/status` no `modules/gui_app.py` retornando JSON
- [X] T010 [US4] Expor rota de API `/api/hardware/load` no `modules/gui_app.py` com suporte ao cache

**Checkpoint**: At this point, User Story 1 and 4 should be fully functional and testable independently

---

## Phase 4: User Story 5 - Invalidação Automática (Priority: P1)

**Goal**: O cache se invalida se o hardware mudar ou 30 dias se passarem

**Independent Test**: Modificar manualmente o JSON (CPU modelo); o app deve descartar o cache na próxima execução.

### Implementation for User Story 5

- [X] T011 [P] [US5] Adicionar lógica comparativa de `validacao` em `modules/hardware.py` que aciona re-scan ao divergir
- [X] T012 [P] [US5] Adicionar verificação de expiração (30 dias) ao arquivo de cache em `modules/hardware.py`

**Checkpoint**: Invalidação automática funcionando

---

## Phase 5: User Story 2 & 3 - Reaplicar Otimizações (Priority: P2)

**Goal**: Permitir reaplicar otimizações individuais ou em lote quando encontradas inativas

**Independent Test**: Desativar algo no registro, checar o status, reaplicar e ver se retorna a verde (ativo)

### Implementation for User Story 2 & 3

- [X] T013 [P] [US2] Criar função `reaplicar_otimizacao(id)` em `modules/otimizacao.py` com criação de ponto de restauração
- [X] T014 [US3] Criar função em lote `reaplicar_todas_inativas()` em `modules/otimizacao.py` chamando a reaplicação individual
- [X] T015 [US2] Adicionar opção interativa de reaplicação no menu da CLI em `modules/cli_app.py`
- [X] T016 [US2] Expor rotas de API `/api/otimizacoes/reaplicar` no `modules/gui_app.py` disparando jobs assíncronos (`job_id`)

**Checkpoint**: At this point, User Stories 1-5 should all work independently

---

## Phase 6: User Story 6 - Forçar Re-scan (Priority: P2)

**Goal**: O técnico pode forçar manualmente o redescoberta do hardware ignorando o cache

**Independent Test**: Clicar em forçar re-scan e confirmar que os dados foram recarregados e o JSON atualizado

### Implementation for User Story 6

- [X] T017 [P] [US6] Criar função `forcar_rescan_hardware()` que remove arquivo JSON e puxa dados novamente em `modules/hardware.py`
- [X] T018 [US6] Adicionar rota `/api/hardware/rescan` no `modules/gui_app.py` rodando assíncrono via `job_id`
- [X] T019 [US6] Adicionar atalho para forçar re-scan na tela de hardware da CLI em `modules/cli_app.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T020 Run quickstart.md validation to ensure end-to-end functionality

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 & US4**: Podem começar pós Phase 2 (Foundational)
- **US5**: Depende da US4 (cache de leitura)
- **US2 & US3**: Dependem da US1 (leitura de status)
- **US6**: Depende da US4 (existência do cache)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, otimizacao.py and hardware.py backend updates can happen in parallel

---

## Implementation Strategy

### MVP First (User Story 1 & 4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: Leitura Básica e Cache
4. **STOP and VALIDATE**: Testar na CLI o novo comando
