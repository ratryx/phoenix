# Implementation Plan: Custom Routine Profiles

## Stage 1: Stabilize Foundation
- **Scope**: Fix the flaky `JobManager` test `test_6_7_resultado_serializavel`. The static `time.sleep(0.1)` must be replaced with a robust polling assertion to prevent false negatives in CI/CD.
- **Expected Files**: `tests/test_jobs.py` (to be modified).
- **Files Not to Modify**: `modules/gui/jobs.py` (production logic is sound).

## Stage 2: Extract Gaming Backend
- **Scope**: Resolve the architectural gap where `optimize_gaming` exists only inline inside `PhoenixAPI`. Extract `executar_otimizacao_gaming(resetar_rede)` into `modules/otimizacao.py`.
- **Expected Files**:
  - `modules/otimizacao.py` [MODIFIED]
  - `modules/gui/api.py` [MODIFIED]
- **Files Not to Modify**: Frontend callers should not notice the refactor.

## Stage 3: Domain Model and Persistence
- **Scope**: Create `ProfileService` to handle CRUD operations, defining Default Profiles registry explicitly, and atomic persistence.
- **Risk Handled**: The installer/non-admin write access to `%PROGRAMDATA%` risk must be investigated here. If unresolvable in standard config, a fallback to `%LOCALAPPDATA%` or a prompt to run as Admin must be scoped.
- **Expected Files**:
  - `modules/core/profile_service.py` [NEW]
  - `tests/test_profile_service.py` [NEW]

## Stage 4: Backend CRUD API
- **Scope**: Expose `obter_profiles`, `criar_profile`, `editar_profile`, and `deletar_profile` inside `PhoenixAPI`.
- **Expected Files**:
  - `modules/gui/api.py` [MODIFIED]
  - `tests/test_profile_api.py` [NEW]

## Stage 5: Backend Executor
- **Scope**: Create `ProfileExecutor` to sequentially map string IDs to atomic backend operations. Handles the `skip_restore_point` flag and automatically invokes `criar_ponto_restauracao` securely. Captures snapshots for `report`.
- **Expected Files**:
  - `modules/core/profile_executor.py` [NEW]
  - `tests/test_profile_executor.py` [NEW]

## Stage 6: API Exposure & Single-Source-Of-Truth Migration
- **Scope**: Expose `executar_profile` inside `PhoenixAPI` with `exclusive_group="system_mutation"`. Internally deprecate `RoutineService.executar()` and re-route `executar_rotina_completa` to call `ProfileExecutor.execute("default-complete")`.
- **Expected Files**:
  - `modules/gui/api.py` [MODIFIED]
  - `modules/core/routine_service.py` [DEPRECATED/REMOVED]

## Stage 7: Routine Profiles Frontend Page
- **Scope**: Build the vanilla HTML/CSS/JS page for listing, creating, and deleting profiles using the new endpoints.
- **Expected Files**:
  - `gui/index.html` [MODIFIED]
  - `gui/js/pages/page_routine_profiles.js` [NEW]
  - `gui/style.css` [MODIFIED]

## Stage 8: Progress, Option B, and Report UI Sync
- **Scope**: Build the progress tracker inside the frontend executor bridge. Implement the "Continuar mesmo assim" Option B fallback loop when `RESTORE_POINT_FAILED` is caught. Ensure the History tab loads the TXT report correctly.
- **Expected Files**:
  - `gui/js/operations/routine_executor.js` [MODIFIED/NEW]

## Stage 9: Automated Tests
- **Scope**: 100% test coverage including mock persistence environments.

## Stage 10: Windows Smoke Testing & Merge
- **Scope**: Execute manual verification to certify the `%PROGRAMDATA%` permissions and Option B flow behavior locally. Pull request to merge into `main`.
