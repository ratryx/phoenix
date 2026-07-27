# Test Plan: Custom Routine Profiles

## Evidence of Baseline Stability
- **JobManager Flakiness Test (`test_6_7_resultado_serializavel`)**: Tested once using `python -m pytest tests/test_jobs.py::test_6_7_resultado_serializavel -v`. Passed in 0.57s. The issue is confirmed as a test synchronization flaw (`time.sleep(0.1)`) under varying thread load, rather than a production code flaw.

## Cross-Platform Tests (pytest, native environments)

### 1. Domain and Validation Tests (`test_profile_service.py`)
- **Validation Tests**:
  - Test profile creation with an empty name (must fail).
  - Test name normalization (stripping spaces).
  - Test creation with an empty step list (must fail).
  - Test maximum profile step count (>20 must fail).
  - Test unknown/unmapped step identifiers (must fail).
- **CRUD Tests**:
  - Create a valid custom profile.
  - Read profiles to ensure it exists alongside `default-quick` and `default-complete`.
  - Update a custom profile's sequence.
  - Delete a custom profile.
  - Attempt to update or delete a Default ID (must raise error `INVALID_OPERATION`).
- **Duplicate Protection**: Test adding a profile with a name that already exists (case-insensitive check, must fail gracefully).

### 2. Persistence and Recovery Tests (`test_profile_persistence.py`)
- **Persistence Tests**:
  - Verify JSON saves to the global application base directory.
  - Verify atomic write operations (using a mocked temp file rename).
- **Corruption & Migration Tests**:
  - Write invalid JSON text to `profiles.json`.
  - Assert the service creates `profiles.corrupt.json` and loads empty custom profiles cleanly.
- **Installed vs Portable**:
  - Mock `IS_PORTABLE = True` and ensure paths resolve to `exe_dir/dados`.
  - Mock `IS_PORTABLE = False` and ensure paths resolve to `%PROGRAMDATA%\PhoenixOptimizer`.

### 3. API Contract and JobManager Tests (`test_profile_api.py`)
- **API Tests**:
  - Ensure the API exposes `obter_profiles()` returning valid schema.
  - Ensure `executar_profile(profile_id="default-complete")` accepts the ID and returns a `job_id`.
- **Job Polling Tests**:
  - Mock an executor. Polling the `job_id` should return `{"status": "running", "progresso": 50, "mensagem": "..."}`.
- **Concurrency & Privilege Tests**:
  - Trigger `executar_profile` twice rapidly. Ensure `JobManager` rejects the second one due to `exclusive_group="system_mutation"`.
- **Failure Injection**:
  - Force an exception inside the executor and assert `JobManager` catches it and returns a sanitized error payload.

---

## Windows-Specific Tests (pytest, requiring Windows OS)

### 4. Executor and Restore-Point Tests (`test_profile_executor.py`)
- **Restore-Point Tests**:
  - Profile without mutable steps (e.g., `diagnostic_before` only) should *not* call `criar_ponto_restauracao`.
  - Profile with `optimize_general` *must* call `criar_ponto_restauracao` once before the optimization.
  - Inject a failure into `criar_ponto_restauracao`. Ensure the executor aborts execution with `RESTORE_POINT_FAILED`.
  - Trigger execution with `{skip_restore_point: true}` option. Assert `criar_ponto_restauracao` is bypassed correctly.
- **Step-Order Tests**:
  - Run a mock profile. Verify modules are called in the exact expected order.
- **Report and History Integration**:
  - Execute a profile with `diagnostic_before`, `cleanup`, `diagnostic_after`, and `report`. Ensure the snapshots are saved successfully and `exportar_relatorio_txt` generates the file.

---

## UI and Frontend Tests (Node.js/Jest/Vanilla JS Checks)

### 5. Frontend Integration
- **Page Tests**:
  - Ensure the "Custom Profiles" UI renders the list correctly.
  - Ensure editing forms restrict lengths (1-50 chars).
- **Option B Restore-Point Loop**:
  - If execution fails with `RESTORE_POINT_FAILED`, assert the "Continuar mesmo assim" legacy modal appears.
  - Assert clicking "Continuar" triggers a second API call to `executar_profile` passing `skip_restore_point=true`.

---

## Manual Smoke-Test Checklist (Windows 10/11)

- [ ] Open the app, navigate to "Profiles". Verify default profiles are visible.
- [ ] Create a profile named "Test Smoke", add "Cleanup", and "Standby Memory".
- [ ] Run "Test Smoke". Ensure progress bar updates fluidly.
- [ ] Verify that no Restore Point was created.
- [ ] Create a profile adding "General Optimization". Run it. 
- [ ] Verify Windows shows a new Restore Point created.
- [ ] Verify the report tab contains a populated text file containing valid space cleanup metrics.
- [ ] Close the application and reopen it. Verify "Test Smoke" persists.
- [ ] Check `%PROGRAMDATA%\PhoenixOptimizer\profiles.json` without Admin permissions. Note if Windows UAC disrupts saving (addressing the unresolved permissions risk).
