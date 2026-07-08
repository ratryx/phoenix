# Tasks: Windows GUI Validation

**Input**: Design documents from `specs/001-validate-gui-windows/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No automated testing requested. All verification is performed manually on Windows.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify project structure matches the implementation plan
- [x] T002 [P] Install requirements from requirements.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T003 Implement `setup_console` function using `ctypes.windll.kernel32.AttachConsole` and redirect stdout/stderr/stdin in `launcher.py`
- [x] T004 Modify `phoenix.spec` to set `console=False`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Executar a GUI sem console visível (Priority: P1) 🎯 MVP

**Goal**: Open GUI via launcher.py / built executable without spawning a cmd terminal popup.

**Independent Test**: Build and double-click executable. Confirm the GUI displays and no console opens.

### Implementation for User Story 1

- [x] T005 [US1] Update `launcher.py` main execution path to bypass choice menu and start GUI mode directly when `setup_console()` returns `False`
- [x] T006 [US1] Compile the executable using PyInstaller command: `pyinstaller phoenix.spec`
- [x] T007 [US1] Manually verify that double-clicking the generated `dist/PhoenixOptimizer.exe` starts the GUI without displaying a black console window

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comunicação Bidirecional e Navegação da GUI (Priority: P1)

**Goal**: Validate full navigation of the 8 pages and JS↔Python bridge execution.

**Independent Test**: Navigate all 8 pages and verify hardware detection and custom window controls work.

### Implementation for User Story 2

- [ ] T008 [US2] Verify customized frameless window dragging (drag bar) works smoothly in GUI mode
- [ ] T009 [US2] Verify page navigation across all 8 GUI pages works without scripting/rendering errors
- [ ] T010 [US2] Verify Python-JS communication by checking the Hardware page loads real system data

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final check and packaging validation

- [ ] T011 Run all validation scenarios listed in `specs/001-validate-gui-windows/quickstart.md`
- [ ] T012 Clean up temporary build artifacts (like `build/` directory) and verify the final setup

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independently testable

### Parallel Opportunities

- T002 (Setup dependencies) can run in parallel with general inspection.
- The verification of US1 (T007) and US2 (T008-T010) are logically sequential since we build the executable in T006, but code changes for T005 (US1) and T008-T010 (US2) can be worked on concurrently if needed.

---

## Parallel Example: User Story 1

```bash
# Verify UI files and Python backend imports in parallel:
Task: "Verify custom frameless window dragging (drag bar) works smoothly in GUI mode"
Task: "Verify page navigation across all 8 GUI pages works without scripting/rendering errors"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Verify the executable opens without terminal popup
5. Proceed to User Story 2
