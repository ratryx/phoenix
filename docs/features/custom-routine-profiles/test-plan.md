# Test Plan: Custom Routine Profiles

## Baseline: JobManager Test Evidence

### Test: `test_6_7_resultado_serializavel`
**Command**: `python -m pytest tests/test_jobs.py::test_6_7_resultado_serializavel -v`

| Run | Result | Duration | Observed Final State |
| --- | --- | --- | --- |
| 1 (prior session) | PASSED | 0.57s | `status: "done"` |
| 2 (this session) | PASSED | 0.57s | `status: "done"` |
| 3 (this session) | PASSED | 0.57s | `status: "done"` |

**Conclusion**: The intermittent failure was not reproduced in 3 executions. The static `time.sleep(0.1)` at lines 54 and 67 of `test_jobs.py` remains a potential synchronization risk. The root cause of the previously reported `running` state is unconfirmed. Production `JobManager` stability is not proven by these executions. Phase 1 must investigate both test synchronization and production state publication without assuming which is defective.

## Cross-Platform Tests (pytest)

### 1. Profile Registry Tests (`test_profile_registry.py`)
- Default profiles (`default-quick`, `default-standard`, `default-gaming`, `default-complete`) are all present and immutable.
- `default-complete` sequence matches `RoutineService.executar()` order.
- Default registry does not import GUI or API modules.

### 2. Domain and Validation Tests (`test_profile_service.py`)
- **Validation**:
  - Empty name → rejected.
  - Name > 50 chars → rejected.
  - Name normalization (strip whitespace).
  - Duplicate name (case-insensitive) → rejected.
  - Empty step list → rejected.
  - Step count > 20 → rejected.
  - Unknown step ID → rejected.
  - `report` not final → rejected.
  - `report` without `diagnostic_before` and `diagnostic_after` → rejected.
  - Custom ID with `default-` prefix → rejected.
- **CRUD**:
  - Create a valid custom profile → UUID assigned.
  - Read profiles → defaults + custom combined.
  - Update custom profile steps → success.
  - Delete custom profile → success.
  - Update default → `DEFAULT_PROFILE_IMMUTABLE`.
  - Delete default → `DEFAULT_PROFILE_IMMUTABLE`.
  - Duplicate default → creates new custom profile.
  - Unknown ID → `PROFILE_NOT_FOUND`.
- **Elevation**:
  - Profile CRUD as a standard user → works successfully (writing to `%LOCALAPPDATA%`).

### 3. Persistence and Recovery Tests (`test_profile_persistence.py`)
- **Installed mode** (mock `IS_PORTABLE=False`):
  - Profiles saved to `%LOCALAPPDATA%/PhoenixOptimizer/profiles.json`.
  - Atomic write: `profiles.tmp.json` → rename to `profiles.json`.
- **Portable mode** (mock `IS_PORTABLE=True`):
  - Profiles saved to `<exe_dir>/dados/profiles.json`.
  - Read-only drive → `PERSISTENCE_WRITE_FAILED`.
  - No silent fallback to installed storage.
- **Corruption**:
  - Invalid JSON → moved to `profiles.corrupt.json`, empty list loaded.
  - Backup rename failure → empty list loaded, error logged.
  - ID with `default-` prefix in file → silently ignored.
- **Directory creation failure** → sanitized error returned.
- **Missing `%LOCALAPPDATA%`** → falls back to `Path.home() / "PhoenixOptimizer"`.

### 4. API Contract Tests (`test_profile_api.py`)
- `obter_profiles()` → returns valid JSON with defaults and customs.
- `criar_profile(name, steps)` → returns new profile with UUID.
- `editar_profile(id, name, steps)` → updates custom profile.
- `deletar_profile(id)` → removes custom profile.
- `executar_profile(profile_id)` → returns `{"job_id": "..."}`.
- `executar_profile` with unknown ID → sanitized error.
- Concurrent `executar_profile` → second rejected by `system_mutation`.
- `resolve_profile_decision(job_id, decision_id, action)` → validated.
- Duplicate decision submission → `DECISION_ALREADY_RESOLVED`.
- Invalid decision ID → `DECISION_NOT_FOUND`.
- Late decision submission (after timeout) → `DECISION_NOT_FOUND` (or expired equivalent).

## Windows-Specific Tests (pytest, requires Windows)

### 5. Executor Tests (`test_profile_executor.py`)
- **Step Order**: Steps execute in profile-defined order.
- **Restore Point**:
  - Profile without RP-requiring steps → `criar_ponto_restauracao` not called.
  - Profile with `optimize_general` → `criar_ponto_restauracao` called once before it.
  - Steps before the RP-requiring step (e.g., `diagnostic_before`, `cleanup`) run first.
  - RP failure → job enters `decision_required` state.
  - `continue_without_restore_point` → execution resumes from pending step.
  - `abort` → execution terminates, no further steps run, status indicates `PROFILE_EXECUTION_ABORTED`.
  - No completed steps are repeated after continuation.
- **Timeouts and Lock Behavior**:
  - Decision resolved before timeout → execution resumes.
  - Decision expires (15 min MVP timeout) → execution terminates as `PROFILE_DECISION_EXPIRED`, no pending steps run.
  - Lock release after `continue` → `system_mutation` released when job ends.
  - Lock release after `abort` → `system_mutation` released.
  - Lock release after expiration → `system_mutation` released.
  - Lock release after internal exception → `system_mutation` released via `finally`.
- **Closures**:
  - Frontend closure while backend remains running → execution remains alive until resolved or timeout.
  - Application restart after an interrupted execution → old job is invalid, decision IDs are invalid.
- **Privilege execution**:
  - Privileged step failure as a standard user → sanitized privilege failure recorded.
- **Progress**:
  - Progress updates deterministically: `(completed / total) * 100`.
  - During `decision_required`, progress does not reset.
- **Report**:
  - Profile with `diagnostic_before`, `cleanup`, `diagnostic_after`, `report` → TXT file generated.
  - Report failure after mutable steps → `ok: false` with `completed_steps` listed.
- **Attendance**: Executor receives `id_atendimento` from API. Does not create its own.
- **Gaming**: `optimize_gaming` calls `executar_otimizacao_gaming(id, resetar_rede=False)`.

## Frontend Tests (Vanilla JS)

### 6. Profile Management Page
- Default profiles listed and not editable/deletable.
- Custom profile CRUD forms enforce name length and step limits.
- Execute button disabled during active execution.

### 7. Decision Modal
- `decision_required` status → modal shown with abort/continue options.
- Clicking the same option twice → only one request sent.
- After decision → polling resumes normally.

## Manual Smoke-Test Checklist (Windows 10/11)

- [ ] Navigate to "Profiles". Default profiles are visible and immutable.
- [ ] Create "Test Smoke" with steps: `cleanup`, `standby_memory`.
- [ ] Run "Test Smoke" as a standard user. Progress bar updates. No restore point created.
- [ ] Create a profile with `optimize_general`. Run it as admin.
- [ ] Verify restore point created before optimization.
- [ ] Close and reopen the app. Verify "Test Smoke" persists.
- [ ] Check `%LOCALAPPDATA%\PhoenixOptimizer\profiles.json` exists and is readable.
- [ ] Simulate RP failure. Verify decision modal appears. Verify continue works.
- [ ] Verify timeout correctly aborts after a configured (shortened for test) period.
- [ ] Run `default-complete`. Verify behavior matches legacy Complete Routine.
