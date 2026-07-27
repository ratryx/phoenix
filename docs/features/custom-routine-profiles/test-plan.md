# Test Plan: Custom Routine Profiles

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
  - Read profiles to ensure it exists.
  - Update a custom profile's sequence.
  - Delete a custom profile.
  - Attempt to update or delete a Default profile (must raise error).
- **Duplicate Protection**: Test adding a profile with a name that already exists (must fail gracefully).

### 2. Persistence and Recovery Tests (`test_profile_persistence.py`)
- **Persistence Tests**:
  - Verify JSON saves to the correct `%PROGRAMDATA%` mock or portable path mock.
  - Verify atomic write operations (using a mocked temp file rename).
- **Corruption & Migration Tests**:
  - Write invalid JSON text to `profiles.json`.
  - Assert the service creates `profiles.corrupt.json` and loads empty custom profiles cleanly.
- **Installed vs Portable**:
  - Mock `IS_PORTABLE = True` and ensure paths resolve to the relative `dados` directory.
  - Mock `IS_PORTABLE = False` and test resolution.

### 3. API Contract and JobManager Tests (`test_profile_api.py`)
- **API Tests**:
  - Ensure the API exposes `obter_profiles()` and returns correctly serialized JSON.
  - Ensure `executar_profile()` accepts an ID and returns a `job_id`.
- **Job Polling Tests**:
  - Mock an executor. Polling the `job_id` should return valid progress and status dictionaries.
- **Concurrency & Privilege Tests**:
  - Trigger `executar_profile` twice rapidly. Ensure `JobManager` rejects the second one due to `exclusive_group="system_mutation"`.
- **Failure Injection**:
  - Force an exception inside the executor and assert `JobManager` catches it and returns a sanitized error payload without revealing source code traces.

---

## Windows-Specific Tests (pytest, requiring Windows OS)

### 4. Executor and Restore-Point Tests (`test_profile_executor.py`)
- **Restore-Point Tests**:
  - Profile without mutable steps (e.g., diagnostic only) should *not* call `criar_ponto_restauracao`.
  - Profile with `optimize_general` *must* call `criar_ponto_restauracao` once.
  - Inject a failure into `criar_ponto_restauracao`. Ensure the executor aborts execution securely.
- **Step-Order Tests**:
  - Run a mock profile with `cleanup` then `standby_memory`. Verify `modules` are called in the exact expected order.
- **Complete Routine Regression**:
  - Execute the default "Complete" profile. Verify it delegates accurately to `RoutineService.executar` without side-effects.
- **Report and History Integration**:
  - Execute a profile with `diagnostic_before` and `report`. Ensure the txt report is correctly dumped into the logs directory and a history session is generated.

---

## UI and Frontend Tests (Node.js/Jest/Vanilla JS Checks)

### 5. Frontend Integration
- **Page Tests**:
  - Ensure the "Custom Profiles" UI renders the list correctly.
  - Ensure editing forms restrict lengths and inputs according to the validation rules.
- **Duplicate-Click Tests**:
  - Prevent the "Execute" button from submitting multiple HTTP requests (button disabling).

---

## Manual Smoke-Test Checklist (Windows 10/11)

- [ ] Open the app, navigate to "Profiles". Verify default profiles are visible and cannot be edited.
- [ ] Create a profile named "Test Smoke", add "Cleanup", and "Standby Memory".
- [ ] Run "Test Smoke". Wait for completion. Ensure progress bar updates fluidly.
- [ ] Verify that no Restore Point was created (not required for these steps).
- [ ] Create a profile adding "General Optimization". Run it. 
- [ ] Verify Windows shows a new Restore Point created.
- [ ] Ensure the generated report appears in the History tab.
- [ ] Close the application and reopen it. Verify "Test Smoke" persists.
- [ ] Switch to a portable drive (simulated). Verify profiles are segregated correctly in the `dados` folder.
