# Architecture Document: Custom Routine Profiles

## Repository Audit Findings
- **JobManager**: Centralized in `modules/gui/jobs.py`. `JobManager` intercepts executions and safely prevents overlapping mutable profiles via `exclusive_group="system_mutation"`.
- **Complete Routine**: `RoutineService` (in `modules/core/routine_service.py`) hardcodes the linear routine sequence but hides internal progress steps. This prevents it from being used dynamically in custom profiles.
- **Gaming Optimization**: Currently scattered inside `modules/gui/api.py`. There is no canonical backend atomic method for Gaming.
- **Persistence Resolution**: `modules.shared.obter_pasta_base()` provides the correct paths, mapping automatically to `%PROGRAMDATA%\PhoenixOptimizer` (Installed) or `exe_dir\dados` (Portable). Standard-user write access to `%PROGRAMDATA%` is an unresolved implementation risk that requires deeper installer investigation during implementation.
- **Restore Point**: Implemented correctly in `otimizacao.py`. PowerShell BYPASS commands are strictly backend-hardcoded, and errors securely cascade up.
- **JobManager Risk**: `tests/test_jobs.py` uses `time.sleep(0.1)` indicating an intermittent race condition where the thread hasn't finished dumping "done". This is a test synchronization flaw, not a production JobManager flaw.

## Operation Mapping & Real Implementation
| Step | Real Module & Class | Real Method | Exists in API? |
| --- | --- | --- | --- |
| `diagnostic_before` | `modules.diagnostico` | `coletar_diagnostico_silencioso()` | Wrapped (`obter_diagnostico`) |
| `cleanup` | `modules.limpeza` | `executar_limpeza_completa()` | Wrapped (`executar_limpeza`) |
| `optimize_general` | `modules.otimizacao` | `executar_otimizacao_geral()` | Wrapped (`executar_otimizacao_geral`) |
| `optimize_gaming` | `modules.otimizacao` | *Gap: Scattered in API. Must be extracted* | Wrapped (`executar_otimizacao_gaming`) |
| `optimize_disk` | `modules.otimizacao` | `otimizar_disco_principal()` | Wrapped (`otimizar_disco`) |
| `standby_memory` | `modules.otimizacao` | `liberar_memoria_standby()` | Wrapped (`liberar_memoria_standby`) |
| `startup_analysis` | `modules.otimizacao` | `analisar_startup()` | Wrapped (`analisar_startup`) |
| `diagnostic_after` | `modules.diagnostico` | `coletar_diagnostico_silencioso()` | Wrapped |
| `report` | `modules.relatorio` | `exportar_relatorio_txt()` | Embedded in `executar_rotina_completa` |

### Architectural Gaps
1. **Gaming Optimization Extraction**: There is no single atomic backend operation for Gaming. The sequence (`ativar_plano_energia`, `ativar_modo_jogo_windows`, `desativar_gamebar`, `otimizar_gpu_para_jogos`) must be extracted into `modules/otimizacao.py` as `executar_otimizacao_gaming(resetar_rede=False)` so `ProfileExecutor` can call it cleanly.
2. **Standard-User `%PROGRAMDATA%` Permissions**: Unresolved risk regarding whether non-admins can save profiles locally if the installer does not grant explicit DACLs.

## Complete Profile Single-Source-of-Truth
The "Complete Profile" default (`default-complete`) acts as the single source of truth for sequences.
Instead of `ProfileExecutor` hiding steps inside `RoutineService.executar`, `default-complete` is explicitly defined as `[diagnostic_before, cleanup, optimize_general, diagnostic_after, report]`.
The executor executes this sequence linearly.
*Compatibility Strategy*: The legacy `RoutineService.executar()` and `PhoenixAPI.executar_rotina_completa` will be deprecated and internally re-routed to invoke `ProfileExecutor.execute("default-complete")`. This guarantees behavior, progress, and execution consistency.

## Persistence and Profile Ownership
Profiles belong to the Application globally, not to individual clients.
- **Path**: `modules.shared.obter_pasta_base(cliente=None) / "profiles.json"`.
- **Atomic Persistence**: Data is written using `json.dump` to `profiles.tmp.json` and cleanly renamed via `os.replace` to prevent mid-write corruption.
- **Recovery**: If `profiles.json` fails `json.load()`, it is moved to `profiles.corrupt.json`. An empty custom profile state is instantiated.

## Frontend / Backend Contract
The frontend invokes `executar_profile(profile_id, options)` and receives a `job_id`.
The API is heavily fortified:
- No module paths or function names exist in the payload.
- Backend resolves `profile_id` against the validated JSON store and Default registries.
- Options: `{ skip_restore_point: boolean }` is allowed to facilitate the legacy Option B UI flow.

## Restore-Point Timing
The executor reads the full profile array. Before invoking `step[i]`, it checks the step's metadata. The *very first time* a step has `requires_rp=True`, the executor halts and invokes `otimizacao.criar_ponto_restauracao()`. Once created successfully, a boolean flag `rp_created_this_session` is set to true to prevent further calls.
If it fails, the executor safely aborts with `status="done", ok=False, codigo="RESTORE_POINT_FAILED"`.

## File Placement & Dependencies
- `modules/core/profile_service.py` [NEW]: Contains `ProfileService` for CRUD.
- `modules/core/profile_executor.py` [NEW]: Contains `ProfileExecutor`.
- `modules/otimizacao.py` [MODIFIED]: Extract gaming operations.
- `modules/gui/api.py` [MODIFIED]: Add `obter_profiles`, `executar_profile`. Re-route `executar_rotina_completa`.
