# Custom Routine Profiles Specification

## Problem Statement
Technicians need to automate repetitive tasks based on specific scenarios (e.g., gaming setups, quick maintenance, deep cleaning). Currently, the "Complete Routine" is hardcoded in `RoutineService`. Technicians waste time manually executing individual operations for cases that do not require the full routine, increasing the risk of skipping crucial steps like diagnostics and reports.

## Goals
- Allow technicians to create, edit, duplicate, and execute custom ordered sequences of existing operations.
- Provide sensible, immutable default profiles for common scenarios.
- Automatically manage Restore Points, diagnostics, and reports.
- Maintain concurrency safety and ensure all execution occurs asynchronously in the backend via `JobManager`.

## Non-Goals
- Cloud synchronization or sharing of profiles.
- Arbitrary scripts, custom PowerShell commands, or software removal capabilities.
- Parallel execution of multiple steps or profiles simultaneously.
- Complex per-step parameters (e.g., selecting specific registry keys or choosing network reset).
- Technician permission levels or external telemetry.

## Profile Ownership and Elevation
Routine profiles are **technician preferences**, not customer or attendance records.
- **Installed mode**: Windows-user-specific. Stored under `%LOCALAPPDATA%`.
- **Portable mode**: Portable-instance-specific. Stored in the portable data directory.

Profiles are never stored inside customer or attendance directories.

**Runtime Elevation**:
The application does not enforce global runtime elevation. While the installer uses `PrivilegesRequired=admin`, there is no application manifest (`requestedExecutionLevel`) or PyInstaller spec enforcing elevation on every launch. Individual mutable operations perform runtime privilege checks (e.g., `ctypes.windll.shell32.IsUserAnAdmin()`).
Because standard-user execution is possible:
- `%LOCALAPPDATA%\PhoenixOptimizer\profiles.json` remains writable without administrator rights.
- Profile CRUD operations do not require elevation.
- Profile execution must report sanitized privilege failures if a step requiring administrator rights is executed by a standard user.

## User Workflow
1. The technician accesses the "Routine Profiles" page.
2. Selects an existing Default Profile or creates a Custom Profile from an allowlisted set of operations.
3. Clicks "Execute".
4. Tracks progress natively as the backend processes the sequence.
5. If a restore-point decision is required, the app pauses and presents abort/continue options.
6. Reviews the generated report in the History tab.

## Allowed Steps
Every step maps to a fixed backend function. No PowerShell command text, Python function names, or module paths are accepted from the frontend.

| Step ID | Backend Module | Backend Function | Mutates | Requires Admin | Requires RP | Report Contribution |
| --- | --- | --- | --- | --- | --- | --- |
| `diagnostic_before` | `modules.diagnostico` | `coletar_diagnostico_silencioso()` | No | No | No | Produces `snapshot_antes` |
| `cleanup` | `modules.limpeza` | `executar_limpeza_completa(id)` | Yes | Yes | No | Produces `espaco_liberado` (bytes) |
| `optimize_general` | `modules.otimizacao` | `executar_otimizacao_geral(id)` | Yes | Yes | Yes | None |
| `optimize_gaming` | `modules.otimizacao` | `executar_otimizacao_gaming(id, resetar_rede=False)` | Yes | Yes | Yes | None |
| `optimize_disk` | `modules.otimizacao` | `otimizar_disco_principal()` | Yes | Yes | No | None |
| `standby_memory` | `modules.otimizacao` | `liberar_memoria_standby()` | Yes | Yes | No | None |
| `startup_analysis` | `modules.otimizacao` | `analisar_startup()` | No | No | No | None |
| `diagnostic_after` | `modules.diagnostico` | `coletar_diagnostico_silencioso()` | No | No | No | Produces `snapshot_depois` |
| `report` | `modules.relatorio` | `exportar_relatorio_txt(antes, depois, mb, path)` | No | No | No | Consumes snapshots and space |

### Gaming Fixed MVP Behavior
The `optimize_gaming` step always invokes `executar_otimizacao_gaming(id_atendimento, resetar_rede=False)`. Network reset is not exposed in the profile schema. If network reset is desired later, it should be treated as a separate allowlisted step or a post-MVP per-step parameter feature.

## Default Profiles
Default profiles have stable string identifiers and are immutable. They are generated programmatically in the backend; they are not stored in `profiles.json`.

| ID | Display Name | Steps |
| --- | --- | --- |
| `default-quick` | Quick Maintenance | `diagnostic_before, cleanup, standby_memory, diagnostic_after, report` |
| `default-standard` | Standard Maintenance | `diagnostic_before, cleanup, optimize_general, optimize_disk, diagnostic_after, report` |
| `default-gaming` | Gaming | `diagnostic_before, cleanup, optimize_gaming, standby_memory, diagnostic_after, report` |
| `default-complete` | Complete | `diagnostic_before, cleanup, optimize_general, diagnostic_after, report` |

The `default-complete` sequence is verified against the current `RoutineService.executar()` implementation: diagnostic_before → cleanup → optimize_general → diagnostic_after → report. This is the single source of truth.

## Profile Schema
- `id`: string. UUID4 for custom profiles. Constant `default-*` prefix for defaults.
- `name`: string. Max 50 characters.
- `is_default`: boolean. `true` for built-in profiles.
- `steps`: array of string identifiers from the step allowlist.

## Profile Lifecycle and CRUD Behavior
- **List**: Combines hardcoded defaults and parsed custom profiles.
- **View**: Displays details and steps.
- **Create**: Generates a new UUID. Name must be 1-50 characters, stripped of leading/trailing whitespace. Duplicate names (case-insensitive) are rejected. Unicode characters are allowed.
- **Edit**: Updates a custom profile. Updating a default ID returns error code `DEFAULT_PROFILE_IMMUTABLE`.
- **Duplicate**: Clones any profile into a new custom UUID, prepending "Cópia de " to the name.
- **Delete**: Removes a custom profile. Deleting a default returns error code `DEFAULT_PROFILE_IMMUTABLE`.
- **Unknown ID**: Returns error code `PROFILE_NOT_FOUND`.
- **Reserved IDs**: Custom profiles cannot use the `default-` prefix. If a persistence file contains an ID starting with `default-`, it is silently ignored during load.

## Validation Rules
- **Empty Profiles**: Rejected.
- **Maximum Steps**: 20 steps per profile.
- **Unknown Steps**: Rejected.
- **Duplicate Steps**: Permitted, except for `report` (max one).
- **Report Rule**: If present, `report` must be the final step.
- **Report Prerequisites**: If a profile contains `report`, it must also contain `diagnostic_before` and `diagnostic_after`. This is enforced by backend validation because the current `exportar_relatorio_txt` requires non-null `snapshot_antes` and `snapshot_depois` dictionaries and will crash if they are missing.

## Execution Behavior
- Profile execution creates an asynchronous job using `JobManager`.
- Only one mutating profile can run at a time (locked by `exclusive_group="system_mutation"`).
- **Attendance Requirement**: Profile execution requires an active attendance (`id_atendimento`). The `PhoenixAPI` already creates attendances via `iniciar_atendimento()`. The executor must receive the `id_atendimento` from the API layer; it must not create its own.

## Progress Contract
The backend sends progress via `JobManager.update_progress()`. The frontend polls via `verificar_tarefa(job_id)`.

**Normal running state:**
```json
{
  "status": "running",
  "progresso": 50,
  "mensagem": "Executando limpeza..."
}
```

Progress is calculated deterministically: `(completed_steps / total_steps) * 100`.

**Decision required state (restore-point failure):**
```json
{
  "status": "decision_required",
  "decision": {
    "id": "<opaque-uuid>",
    "type": "restore_point_failed",
    "allowed_actions": ["abort", "continue_without_restore_point"]
  },
  "current_step": {
    "id": "optimize_general",
    "index": 3,
    "total": 6
  },
  "progresso": 33,
  "mensagem": "Ponto de restauração falhou. Aguardando decisão."
}
```

**Successful completion:**
```json
{
  "status": "done",
  "resultado": { "ok": true, "id_atendimento": "...", "relatorio_txt": "..." }
}
```

**Partial failure (step failed after successful steps):**
```json
{
  "status": "done",
  "resultado": {
    "ok": false,
    "erro": "Não foi possível concluir a operação.",
    "detalhe": "Um erro inesperado ocorreu.",
    "completed_steps": ["diagnostic_before", "cleanup"],
    "failed_step": "optimize_general"
  }
}
```

**Report failure after successful mutable steps:** The executor preserves all completed step results and returns `ok: false` with the completed steps listed. Successful mutable changes are not rolled back.

## Restore-Point Behavior
- **Policy**: The executor inspects the step metadata. Immediately before the *first* step where `requires_rp` is true, it requests a restore point via `otimizacao.criar_ponto_restauracao()`.
- If previous steps (e.g. `diagnostic_before`, `cleanup`) do not require a restore point, they execute normally first.
- Once a restore point is successfully created, a boolean flag prevents further calls during the same execution.

### Decision-Based Continuation
When restore-point creation fails:

1. The current profile execution pauses. Previously completed steps remain completed.
2. The executor generates an opaque `decision_id` (UUID) tied to the current job, the pending step, and the restore-point failure.
3. The job transitions to `status: "decision_required"`.
4. A **15-minute backend timeout** begins.
5. The frontend presents two options: abort or continue without restore point.
6. The frontend submits the decision via:
   ```python
   resolve_profile_decision(job_id: str, decision_id: str, action: str) -> dict
   ```
   Allowed `action` values are backend-controlled: `"abort"` or `"continue_without_restore_point"`.
7. The backend validates:
   - The `job_id` references an active paused job.
   - The `decision_id` matches the pending decision.
   - The token has not already been consumed.
   - The decision has not expired.
   - The pending step has not already started.
8. If `continue_without_restore_point`: execution resumes from the pending step. No completed steps are repeated.
9. If `abort`: execution terminates, the job completes with `ok: false`, and the status indicates `PROFILE_EXECUTION_ABORTED`.
10. If the **15-minute timeout expires**:
    - The pending decision becomes invalid.
    - Execution terminates as aborted (`PROFILE_DECISION_EXPIRED`).
    - The pending mutable step is not started.
    - Later submissions using the decision ID return an expired-decision error.
11. Duplicate submissions are rejected idempotently (`DECISION_ALREADY_RESOLVED`).

### Decision Pause State Ownership and UI Closure
The paused state (decision context, pending step, continuation event) is owned by `ProfileExecutor`, not by the generic `JobManager`. `JobManager` does not currently support paused decisions. The executor thread blocks on a `threading.Event` with a timeout, while awaiting the decision. The `resolve_profile_decision` API signals the event.

- **Frontend Closure (UI Window closes, but Python process is alive)**: The backend execution context remains alive until resolved or expired. Reopening the interface may recover the current job state through existing `JobManager.consultar(job_id)` polling (if the frontend implements state recovery via local storage of active `job_id`s, though this may be limited by MVP frontend design).
- **Process Termination (Python process closes)**: The in-memory paused execution is lost. Operating-system locks disappear with the process. The next application launch must not treat the old execution as active. An old decision ID must never become valid after restart. Durable execution state recovery across restarts is out of scope for MVP.

### Lock Behavior (`system_mutation`)
- **Acquisition**: The `system_mutation` exclusive group lock is acquired by the `JobManager` when the execution begins.
- **Holding**: It remains held while the restore-point decision is pending to prevent concurrent mutable operations from modifying the system state while the user is deciding.
- **Guaranteed Release**: The lock is released in a guaranteed cleanup path (`finally` block) when the job finishes. This release occurs securely after `continue`, `abort`, `timeout`, internal failure, or process termination.
- **Safety**: A duplicate decision cannot release the lock twice. Read-only operations may continue concurrently only if current `JobManager` policy permits them.

### Partial Execution and History
When an execution terminates early (user aborts, decision expires, Python process terminates, or a step fails):
- The final result preserves the list of `completed_steps` IDs.
- The `failed_step` or pending step ID is recorded.
- Start and end timestamps are preserved.
- The sanitized failure code is returned (e.g. `PROFILE_DECISION_EXPIRED`, `PROFILE_EXECUTION_ABORTED`).
- The `report` path is included *only* if the report was successfully generated.
- *Note on Process Termination*: If the Python process forcefully terminates, durable history relies on existing `logs.py` which currently writes snapshots sequentially but does not persist incomplete generic job objects. The history tab will show whatever actions were completed and registered via `logs.registrar_acao()`. Generating a durable "interrupted profile" status record is out of MVP scope unless the existing `JobManager`/`logs.py` already handles it.

## Report and History Contracts

### Attendance
- `logs.gerar_id_atendimento()` returns a timestamp-based string (`YYYYMMDD_HHMMSS`). Source: [logs.py L41-43](file:///c:/Users/Thiago/Desktop/projetos/phoenix-optimizer/modules/logs.py#L41-L43).
- `PhoenixAPI.iniciar_atendimento()` creates the attendance and stores it in `self._id_atendimento`. Source: [api.py L69-72](file:///c:/Users/Thiago/Desktop/projetos/phoenix-optimizer/modules/gui/api.py#L69-L72).
- The executor does not create attendances. The API layer must ensure `id_atendimento` is set before invoking the executor.

### Snapshot Storage
- `logs.salvar_snapshot(id_atendimento, "antes", dados, nome_cliente)` writes `{id}_antes.json`. Source: [logs.py L46-66](file:///c:/Users/Thiago/Desktop/projetos/phoenix-optimizer/modules/logs.py#L46-L66).
- `logs.carregar_snapshot(id_atendimento, "antes")` returns `None` if the file does not exist. Source: [logs.py L69-76](file:///c:/Users/Thiago/Desktop/projetos/phoenix-optimizer/modules/logs.py#L69-L76).

### Report Generation
- `relatorio.exportar_relatorio_txt(snapshot_antes, snapshot_depois, espaco_liberado_mb, caminho_saida)` requires non-null dict arguments. Source: [relatorio.py L115-150](file:///c:/Users/Thiago/Desktop/projetos/phoenix-optimizer/modules/relatorio.py#L115-L150).
- It accesses `snapshot_antes["dados"]` directly at line 117. Passing `None` will crash with a `TypeError`.
- **Consequence**: A profile containing `report` must also contain `diagnostic_before` and `diagnostic_after`. This is enforced by backend validation, not by silent fallback.

### What Happens If...
- **Report is omitted**: No report file is generated. Snapshots and cleanup metrics are still saved if those steps ran. The history tab shows the attendance log but no report.
- **Report is requested without diagnostics**: Rejected by backend validation at profile creation and at execution time.
- **Report generation fails after mutable steps succeeded**: Mutable changes are preserved. The job completes with `ok: false` and lists `completed_steps` and `failed_step: "report"`.
- **Report file writing fails**: Same as above. The job returns a sanitized IO error.
- **Report succeeds but history persistence fails**: The executor catches the error and returns `ok: false` with the completed steps. The report file may exist on disk even though the job result indicates failure.

## Persistence

### Installed Mode
- **Path**: `%LOCALAPPDATA%\PhoenixOptimizer\profiles.json`.
- **Rationale**: Profiles are technician preferences. `%LOCALAPPDATA%` is always writable by the current Windows user without administrator privileges. The existing codebase uses `%PROGRAMDATA%` for logs and rollback data (shared machine-wide records), but profiles are personal configuration. Standard users can create, edit, and save custom profiles.
- **Missing environment variable**: Falls back to `Path.home() / "PhoenixOptimizer"`.

### Portable Mode
- **Detection**: `IS_PORTABLE` is `True` when a sentinel file named `PORTABLE` exists next to the executable. Source: [shared.py L7-12](file:///c:/Users/Thiago/Desktop/projetos/phoenix-optimizer/modules/shared.py#L7-L12).
- **Path**: `<exe_dir>/dados/profiles.json`. This is the real portable data directory used by `obter_pasta_base(cliente=None)` which returns `obter_pasta_exe() / 'dados'`. Source: [shared.py L22-23](file:///c:/Users/Thiago/Desktop/projetos/phoenix-optimizer/modules/shared.py#L22-L23).
- **Read-only drive**: If the portable directory is read-only, saving returns a sanitized error `PERSISTENCE_WRITE_FAILED`. No silent fallback to installed storage.

### Atomic Writes
- Data is written to `profiles.tmp.json` and renamed via `os.replace()` to `profiles.json`.
- If the rename fails, the error is returned to the caller.

### Corruption Recovery
- If `profiles.json` fails `json.load()`, the corrupted file is moved to `profiles.corrupt.json`.
- A fresh empty custom profile list is used.
- Default profiles remain available because they are hardcoded.
- If the backup rename also fails (e.g., disk full), the error is logged and an empty list is returned.
- If both `profiles.json` and `profiles.corrupt.json` exist and both are corrupted, the service loads an empty list and overwrites both on next save.

## Sanitized Errors
All errors returned to the frontend are sanitized. They must not contain:
- Python tracebacks.
- Filesystem paths.
- PowerShell command text.
- Python function or module names.
- Internal exception class names.

Error codes use stable string identifiers (e.g., `PROFILE_NOT_FOUND`, `DEFAULT_PROFILE_IMMUTABLE`, `RESTORE_POINT_FAILED`, `PERSISTENCE_WRITE_FAILED`, `DECISION_ALREADY_RESOLVED`, `PROFILE_DECISION_EXPIRED`, `PROFILE_EXECUTION_ABORTED`).
