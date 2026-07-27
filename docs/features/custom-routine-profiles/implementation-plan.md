# Implementation Plan: Custom Routine Profiles

## Stage 1: Investigate the possible JobManager test instability
- **Scope**: Identify and stabilize the flaky `test_6_7_resultado_serializavel` test to ensure the foundation is solid before adding complex `ProfileExecutor` jobs. The audit identified an insufficient `time.sleep(0.1)` inside the test which causes intermittent failures.
- **Expected Files**: 
  - `tests/test_jobs.py` (to be modified during execution).
- **Files Not to Modify**: 
  - `modules/gui/jobs.py`
  - Production code.
- **Acceptance Criteria**: The test passes 10/10 times locally without modifying production code.
- **Risks**: Modifying tests may mask real race conditions, so only the timing logic must be corrected using a proper polling assertion loop.
- **Review Gate**: Stop and require code review of the test fix before proceeding.
- **Commit Message**: `test: stabilize JobManager serialization test`

## Stage 2: Domain Model and Persistence
- **Scope**: Create `ProfileService` to handle CRUD operations, schema definitions, and atomic persistence of custom profiles.
- **Expected Files**:
  - `modules/core/profile_service.py` [NEW]
  - `tests/test_profile_service.py` [NEW]
- **Files Not to Modify**: Frontend, API.
- **Acceptance Criteria**: All CRUD operations pass in unit tests. Corruption recovery accurately loads an empty profile list.
- **Commit Message**: `feat(core): implement profile domain model and persistence`

## Stage 3: Backend CRUD API
- **Scope**: Integrate `ProfileService` into `PhoenixAPI` to expose profile data securely to the frontend.
- **Expected Files**:
  - `modules/gui/api.py` [MODIFIED]
  - `tests/test_profile_api.py` [NEW]
- **Acceptance Criteria**: The pywebview backend properly responds to `obter_profiles`, `criar_profile`, `editar_profile`, and `deletar_profile`.
- **Commit Message**: `feat(api): expose routine profiles CRUD endpoints`

## Stage 4: Backend Executor
- **Scope**: Create `ProfileExecutor` to map string IDs to actual operations and generate restore points when required.
- **Expected Files**:
  - `modules/core/profile_executor.py` [NEW]
  - `tests/test_profile_executor.py` [NEW]
- **Acceptance Criteria**: The executor runs mock profiles step-by-step asynchronously and delegates the "Complete" profile to `RoutineService`.
- **Commit Message**: `feat(core): implement custom profile executor logic`

## Stage 5: API Exposure (Executor)
- **Scope**: Expose `executar_profile` inside `PhoenixAPI`, delegating to `JobManager` using `exclusive_group="system_mutation"`.
- **Expected Files**:
  - `modules/gui/api.py` [MODIFIED]
- **Acceptance Criteria**: The `executar_profile` endpoint returns a valid `job_id` and securely wraps the executor logic.
- **Commit Message**: `feat(api): expose profile execution endpoint`

## Stage 6: Routine Profiles Frontend Page
- **Scope**: Build the vanilla HTML/CSS/JS page for listing, editing, creating, and deleting profiles.
- **Expected Files**:
  - `gui/index.html` [MODIFIED]
  - `gui/js/pages/page_routine_profiles.js` [NEW]
  - `gui/style.css` [MODIFIED]
- **Acceptance Criteria**: UI correctly lists and manipulates profiles without allowing modification of Defaults.
- **Commit Message**: `feat(ui): implement routine profiles management page`

## Stage 7: Progress, Report, and History Integration
- **Scope**: Build the progress tracker inside the frontend executor bridge and ensure reports dump correctly to the frontend view on completion.
- **Expected Files**:
  - `gui/js/operations/routine_executor.js` [MODIFIED/NEW]
- **Acceptance Criteria**: A complete custom profile run correctly displays a fluid progress bar and populates the History tab upon success.
- **Commit Message**: `feat(ui): integrate progress tracking and reports for custom profiles`

## Stage 8: Automated Tests
- **Scope**: Add any missing end-to-end Python integration tests combining `PhoenixAPI`, `ProfileExecutor`, and `JobManager`.
- **Expected Files**:
  - `tests/test_profile_integration.py` [NEW]
- **Acceptance Criteria**: Total 100% test passing in both Python and Node suites.
- **Commit Message**: `test: complete integration testing for routine profiles`

## Stage 9: Windows Smoke Testing
- **Scope**: Manually perform the Smoke Test Checklist identified in `test-plan.md` on a Windows machine.
- **Acceptance Criteria**: Visual confirmation that restore points trigger correctly and operations pass.

## Stage 10: Controlled Merge
- **Scope**: Merge `feat/custom-routine-profiles` into `main` keeping a clean history.
- **Review Gate**: Full pull request approval required.
- **Commit Message**: `merge: integrate custom routine profiles feature`
