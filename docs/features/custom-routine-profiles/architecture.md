# Architecture Document: Custom Routine Profiles

## Repository Audit Findings

### JobManager
Centralized in `modules/gui/jobs.py`. Manages async jobs with `threading.RLock`, TTL-based cleanup, and `exclusive_group` locking. The `consultar()` method returns `status`, `resultado`, and optional `progresso`/`mensagem` fields. It does not support paused states or decision callbacks natively.

### RoutineService
Located in `modules/core/routine_service.py`. Defines the Complete Routine as a linear hardcoded sequence: `diagnostic_before → cleanup → optimize_general → diagnostic_after → report`. Requires `id_atendimento` as a mandatory argument.

### Gaming Optimization
A canonical backend function `executar_otimizacao_gaming(id_atendimento, resetar_rede)` already exists in `modules/otimizacao.py` at line 448. It invokes: `ativar_plano_energia_alto_desempenho()`, `ativar_modo_jogo_windows()`, `desativar_gamebar_overlay()`, `otimizar_gpu_para_jogos()`, and conditionally `limpar_dns_e_rede()`.

However, `PhoenixAPI.executar_otimizacao_gaming()` at line 188 of `api.py` duplicates this sequence inline rather than delegating to the module-level function. This is an existing inconsistency in the codebase. The `ProfileExecutor` must call the module-level function directly and must not duplicate the sequence a third time.

### Persistence Paths
`modules/shared.py` provides `obter_pasta_base(cliente=None)`:
- **Installed**: `%PROGRAMDATA%/PhoenixOptimizer` (line 33). Used for logs, cache, and rollback.
- **Portable**: `obter_pasta_exe() / 'dados'` (line 23).

Profiles use a **different** path because they are technician preferences, not machine-wide records:
- **Installed**: `%LOCALAPPDATA%/PhoenixOptimizer/profiles.json`.
- **Portable**: `<exe_dir>/dados/profiles.json`.

### Installer Evidence
The Inno Setup script (`phoenix_setup.iss`) specifies:
- `PrivilegesRequired=admin` (line 45): The installer runs as admin.
- `DefaultDirName={autopf}\Phoenix Optimizer` (line 40): Installs to Program Files.
- No `[Dirs]` section exists. No explicit `%PROGRAMDATA%` directory creation or DACL configuration.
- The `[UninstallDelete]` comment (lines 85-89) mentions `%PROGRAMDATA%\PhoenixOptimizer` for logs but does not create it.
- The application itself creates `%PROGRAMDATA%\PhoenixOptimizer` directories on first use via `mkdir(parents=True, exist_ok=True)` calls in `logs.py` and `shared.py`.
- **Risk**: Since the app requires admin (`PrivilegesRequired=admin`), the current `%PROGRAMDATA%` usage works because the app always runs elevated. However, if the app is ever run without elevation, `%PROGRAMDATA%` writes would fail. Profiles using `%LOCALAPPDATA%` avoid this risk entirely.

### Restore Point
Implemented in `modules/otimizacao.py` via `criar_ponto_restauracao()` (line 173). Uses fixed PowerShell commands hardcoded in the backend. Returns structured error codes: `NO_ADMIN`, `LIMIT_EXCEEDED`, `RESTORE_DISABLED`, `TIMEOUT`, `UNKNOWN`.

### JobManager Test Risk
`tests/test_jobs.py::test_6_7_resultado_serializavel` uses `time.sleep(0.1)` at lines 54 and 67 to wait for job completion. Test results (3 total executions across this review):

| Run | Command | Result | Duration |
| --- | --- | --- | --- |
| 1 | `python -m pytest tests/test_jobs.py::test_6_7_resultado_serializavel -v` | PASSED | 0.57s |
| 2 | Same | PASSED | 0.57s |
| 3 | Same | PASSED | 0.57s |

**Conclusion**: The intermittent failure was not reproduced in 3 executions. The static `time.sleep(0.1)` remains a potential synchronization risk under heavy system load or slower hardware. The root cause of the previously reported `running` observation is unconfirmed. Production `JobManager` stability is not proven by these executions alone. Phase 1 must investigate both the test synchronization and production state publication without assuming which one is defective.

## Operation Mapping

| Step ID | Real Module | Real Method | Exists as API Endpoint | Creates Own Job |
| --- | --- | --- | --- | --- |
| `diagnostic_before` | `modules.diagnostico` | `coletar_diagnostico_silencioso()` | Yes (`obter_diagnostico`) | Yes (wrapped) |
| `cleanup` | `modules.limpeza` | `executar_limpeza_completa(id)` | Yes (`executar_limpeza`) | Yes (wrapped) |
| `optimize_general` | `modules.otimizacao` | `executar_otimizacao_geral(id)` | Yes (`executar_otimizacao_geral`) | Yes (wrapped) |
| `optimize_gaming` | `modules.otimizacao` | `executar_otimizacao_gaming(id, resetar_rede=False)` | Yes (`executar_otimizacao_gaming`) | Yes (wrapped) |
| `optimize_disk` | `modules.otimizacao` | `otimizar_disco_principal()` | Yes (`otimizar_disco`) | Yes (wrapped) |
| `standby_memory` | `modules.otimizacao` | `liberar_memoria_standby()` | Yes (`liberar_memoria_standby`) | Yes (wrapped) |
| `startup_analysis` | `modules.otimizacao` | `analisar_startup()` | Yes (`analisar_startup`) | Yes (wrapped) |
| `diagnostic_after` | `modules.diagnostico` | `coletar_diagnostico_silencioso()` | Same as `diagnostic_before` | Same |
| `report` | `modules.relatorio` | `exportar_relatorio_txt(antes, depois, mb, path)` | Embedded in `executar_rotina_completa` | No |

**Key finding**: Every existing API endpoint wraps the module function in its own `JobManager` job. The `ProfileExecutor` must NOT call these API endpoints internally and must NOT create nested independent jobs. It operates as a single job that calls the underlying module functions directly in sequence.

## Complete Profile Single-Source-of-Truth

### Dependency Direction
```
Immutable Default Profile Registry (data only, no imports)
        ↓
ProfileService (resolver, validator, CRUD)
        ↓
ProfileExecutor (step runner, RP policy, progress)
        ↑
Legacy Complete Routine adapter (optional compatibility shim)
```

The `default-complete` profile is defined as an immutable data structure:
```python
{"id": "default-complete", "name": "Completa", "is_default": True,
 "steps": ["diagnostic_before", "cleanup", "optimize_general", "diagnostic_after", "report"]}
```

This sequence is verified against the current `RoutineService.executar()` (lines 55-79 of `routine_service.py`): it performs exactly diagnostic → cleanup → optimize_general → diagnostic → report, in that order.

### Compatibility Strategy
- `ProfileExecutor` must not depend on `RoutineService`.
- `RoutineService` may become a compatibility adapter over `ProfileExecutor` in a future stage.
- The legacy `executar_rotina_completa` endpoint in `PhoenixAPI` remains available during MVP. It may internally delegate to `ProfileExecutor.execute("default-complete")` or continue using `RoutineService` until a separate migration removes it.
- The default profile registry must not import GUI or API modules.
- `ProfileExecutor` calls module-level functions (`modules.diagnostico`, `modules.limpeza`, `modules.otimizacao`, `modules.relatorio`, `modules.logs`) directly.

## Restore-Point Continuation Architecture

The generic `JobManager` does not support paused decisions. Continuation state is owned by `ProfileExecutor`.

### Implementation Concept
1. The executor thread runs inside a `JobManager` job.
2. When a restore-point failure occurs, the executor:
   - Generates an opaque `decision_id` (UUID).
   - Stores the decision context (pending step, allowed actions) in a thread-safe structure.
   - Updates the job's progress fields to expose `decision_required` status.
   - Blocks on a `threading.Event`.
3. The frontend polls and sees `status: "decision_required"`.
4. The frontend calls `resolve_profile_decision(job_id, decision_id, action)`.
5. The API validates the decision and signals the `threading.Event`.
6. The executor thread resumes from the pending step (or aborts).
7. While paused, `system_mutation` remains locked. No other mutable job can start.

### API Contract
```python
resolve_profile_decision(job_id: str, decision_id: str, action: str) -> dict
```
- `action` is an enum: `"abort"` or `"continue_without_restore_point"`.
- Returns `{"ok": true}` on success.
- Returns `{"ok": false, "erro": "...", "codigo": "DECISION_ALREADY_RESOLVED"}` on duplicate.
- Returns `{"ok": false, "erro": "...", "codigo": "DECISION_NOT_FOUND"}` if invalid.

## File Placement and Dependencies

### New Files
- `modules/core/profile_registry.py` [NEW]: Immutable default profile definitions. No imports from GUI or API.
- `modules/core/profile_service.py` [NEW]: CRUD, validation, persistence. Depends on registry and `modules.shared`.
- `modules/core/profile_executor.py` [NEW]: Step execution, RP policy, progress, decision pause. Depends on registry and module-level operation functions.
- `tests/test_profile_service.py` [NEW]
- `tests/test_profile_executor.py` [NEW]
- `tests/test_profile_api.py` [NEW]
- `gui/js/pages/page_routine_profiles.js` [NEW]

### Modified Files
- `modules/gui/api.py` [MODIFIED]: Add `obter_profiles`, `criar_profile`, `editar_profile`, `deletar_profile`, `executar_profile`, `resolve_profile_decision`.
- `gui/index.html` [MODIFIED]: Add navigation entry.
- `gui/style.css` [MODIFIED]: Add profile page styles.

### Unchanged
- `modules/otimizacao.py`: The canonical `executar_otimizacao_gaming` already exists. The API duplication is a pre-existing issue outside the scope of this feature.
- `modules/core/routine_service.py`: Remains unchanged during MVP. May be refactored in a future migration.
