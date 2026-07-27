# Implementation Plan: Custom Routine Profiles

## Stage 1: Investigate JobManager Test Stability
- **Scope**: Investigate `test_6_7_resultado_serializavel` without assuming whether the defect is in the test synchronization or production code. Run the test under load, review the `time.sleep(0.1)` pattern, and determine whether a polling assertion is needed or whether the production `JobManager` has a state publication race.
- **Expected Files**: `tests/test_jobs.py` (may be modified). `modules/gui/jobs.py` (inspected only; modified only if a production race is confirmed).
- **Review Gate**: Stop and present findings before applying any fix.
- **Commit**: `test: investigate JobManager serialization test stability`

## Stage 2: Resolve Installed-Mode Profile Storage
- **Scope**: Introduce a `obter_pasta_perfis()` utility for profile-specific storage. Installed mode uses `%LOCALAPPDATA%\PhoenixOptimizer`. Portable mode uses `<exe_dir>/dados`. Verify directory creation, write permissions, and missing-variable fallback.
- **Expected Files**:
  - `modules/shared.py` [MODIFIED]: Add `obter_pasta_perfis()`.
- **Tests**: Unit test confirming path resolution under both modes.
- **Review Gate**: Code review before proceeding.
- **Commit**: `feat(shared): add profile-specific storage path`

## Stage 3: Establish Immutable Default Profile Registry
- **Scope**: Create `profile_registry.py` containing the four default profile definitions as pure data. No imports from GUI or API modules. Verify `default-complete` matches `RoutineService.executar()` sequence.
- **Expected Files**:
  - `modules/core/profile_registry.py` [NEW]
  - `tests/test_profile_registry.py` [NEW]
- **Review Gate**: Code review of registry data.
- **Commit**: `feat(core): establish immutable default profile registry`

## Stage 4: Implement Profile Persistence and CRUD
- **Scope**: Create `ProfileService` handling CRUD, validation, atomic JSON persistence, and corruption recovery. Uses `obter_pasta_perfis()` for storage and `profile_registry` for defaults.
- **Expected Files**:
  - `modules/core/profile_service.py` [NEW]
  - `tests/test_profile_service.py` [NEW]
  - `tests/test_profile_persistence.py` [NEW]
- **Review Gate**: Code review of validation rules and persistence logic.
- **Commit**: `feat(core): implement profile service with CRUD and persistence`

## Stage 5: Expose Profile CRUD via API
- **Scope**: Add `obter_profiles`, `criar_profile`, `editar_profile`, `deletar_profile` to `PhoenixAPI`.
- **Expected Files**:
  - `modules/gui/api.py` [MODIFIED]
  - `tests/test_profile_api.py` [NEW]
- **Review Gate**: Code review of API surface.
- **Commit**: `feat(api): expose profile CRUD endpoints`

## Stage 6: Implement Profile Executor with Restore-Point Continuation
- **Scope**: Create `ProfileExecutor` that:
  - Runs steps sequentially using module-level functions (not API endpoints).
  - Calculates and emits deterministic progress.
  - Triggers `criar_ponto_restauracao()` before the first `requires_rp` step.
  - On RP failure, pauses via `threading.Event` and exposes `decision_required` state.
  - Accepts `resolve_profile_decision()` to resume or abort.
  - Does not create nested jobs.
  - Does not depend on `RoutineService`.
  - Receives `id_atendimento` from caller.
  - Uses `optimize_gaming` with `resetar_rede=False`.
- **Expected Files**:
  - `modules/core/profile_executor.py` [NEW]
  - `tests/test_profile_executor.py` [NEW]
- **Review Gate**: Code review of continuation logic and error handling.
- **Commit**: `feat(core): implement profile executor with RP continuation`

## Stage 7: Expose Execution and Decision API
- **Scope**: Add `executar_profile(profile_id)` and `resolve_profile_decision(job_id, decision_id, action)` to `PhoenixAPI`. Execution uses `exclusive_group="system_mutation"`.
- **Expected Files**:
  - `modules/gui/api.py` [MODIFIED]
- **Review Gate**: Code review of execution and decision API.
- **Commit**: `feat(api): expose profile execution and decision endpoints`

## Stage 8: Frontend Profile Management Page
- **Scope**: Build the vanilla HTML/CSS/JS page for listing, creating, editing, duplicating, and deleting profiles.
- **Expected Files**:
  - `gui/index.html` [MODIFIED]
  - `gui/js/pages/page_routine_profiles.js` [NEW]
  - `gui/style.css` [MODIFIED]
- **Review Gate**: Visual review.
- **Commit**: `feat(ui): implement routine profiles management page`

## Stage 9: Frontend Execution, Progress, and Decision UI
- **Scope**: Build the execution flow: progress bar, `decision_required` modal with abort/continue options, and report display on completion.
- **Expected Files**:
  - `gui/js/operations/profile_executor.js` [NEW]
- **Review Gate**: Visual and functional review.
- **Commit**: `feat(ui): implement profile execution UI with decision modal`

## Stage 10: Integration Tests
- **Scope**: End-to-end tests combining `PhoenixAPI`, `ProfileExecutor`, `ProfileService`, and `JobManager`.
- **Expected Files**:
  - `tests/test_profile_integration.py` [NEW]
- **Commit**: `test: complete integration testing for routine profiles`

## Stage 11: Windows Smoke Testing
- **Scope**: Execute manual smoke-test checklist from `test-plan.md` on Windows 10/11.
- **Review Gate**: All manual checks pass.

## Stage 12: Controlled Merge
- **Scope**: Merge `feat/custom-routine-profiles` into `main` via pull request.
- **Review Gate**: Full PR approval.
- **Commit**: `merge: integrate custom routine profiles feature`

## Unresolved Risks Tracked for Implementation
1. **JobManager test intermittency**: Root cause unconfirmed. Must be investigated in Stage 1 without assuming the defect location.
2. **API gaming duplication**: `PhoenixAPI.executar_otimizacao_gaming()` duplicates `otimizacao.executar_otimizacao_gaming()` inline. Pre-existing inconsistency outside the scope of this feature but relevant if the API method is ever refactored.
3. **Application restart during decision pause**: The paused job and its decision context are lost. The user must restart the profile manually.
