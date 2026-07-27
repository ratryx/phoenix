# Architecture Document: Custom Routine Profiles

## Repository Audit Findings
- **JobManager**: Resides in `modules/gui/jobs.py`. It correctly implements asynchronous background task execution, managing locks and exclusive groups (`system_mutation`).
- **RoutineService**: Found in `modules/core/routine_service.py`. It orchestrates the Complete Routine linearly.
- **Persistence Paths**: Discovered in `modules/shared.py`. Handles resolution for portable mode (`exe_dir/dados`) and installed mode (`%PROGRAMDATA%/PhoenixOptimizer`).
- **Restore Point**: Implemented in `modules/otimizacao.py` via `criar_ponto_restauracao()`, invoking PowerShell and emitting robust error codes.
- **JobManager Test Risk**: `tests/test_jobs.py` contains a sleep-based timing risk (`time.sleep(0.1)`), causing intermittent false positives where jobs appear `running` when they should be `done`.

## Operation Mapping

| Conceptual Step | Real Module | Function/Method | Mutates | Creates Job Directly? | Requires RP? |
| --- | --- | --- | --- | --- | --- |
| `diagnostic_before` | `modules.diagnostico` | `coletar_diagnostico_silencioso()` | No | No (Wrapped) | No |
| `cleanup` | `modules.limpeza` | `executar_limpeza_completa()` | Yes | No (Wrapped) | No |
| `optimize_general` | `modules.otimizacao` | `executar_otimizacao_geral()` | Yes | No (Wrapped) | Yes |
| `optimize_gaming` | `modules.otimizacao` | (Multiple specific functions) | Yes | No (Wrapped) | Yes |
| `optimize_disk` | `modules.otimizacao` | `otimizar_disco_principal()` | Yes | No (Wrapped) | No |
| `standby_memory` | `modules.otimizacao` | `liberar_memoria_standby()` | Yes | No (Wrapped) | No |
| `startup_analysis`| `modules.otimizacao` | `analisar_startup()` | No | No (Wrapped) | No |
| `diagnostic_after`| `modules.diagnostico` | `coletar_diagnostico_silencioso()` | No | No (Wrapped) | No |
| `report` | `modules.relatorio` | `exportar_relatorio_txt()` | No | No (Wrapped) | No |

## Proposed Components and Responsibilities
- **ProfileService (`modules/core/profile_service.py`)**: Responsible for CRUD operations on custom profiles. Validates schema and handles persistence.
- **ProfileExecutor (`modules/core/profile_executor.py`)**: Converts a `profile_id` into a sequence of Python operations. Generates the restore point if required, runs the sequence, calculates progress, and handles errors. Absorbs or wraps `RoutineService` for the Complete Profile.
- **PhoenixAPI (`modules/gui/api.py`)**: Exposes two new endpoints: `obter_profiles()` and `executar_profile(profile_id: str)`.
- **JSON Storage**: Uses atomic write patterns (write to temp file, replace) inside `modules.shared.obter_pasta_base()`.

## Persistence Strategy
Custom profiles will be stored in `profiles.json` within the application's base data directory (`obter_pasta_base()`). 
- **Atomic Writes**: Data is serialized to a `.tmp` file and then renamed to `profiles.json` to prevent corruption during power loss.
- **Corruption Recovery**: If `json.load` fails, the file is moved to `profiles.corrupt.json` and a fresh file is created.

## Default Profile Strategy
Default profiles (Quick, Standard, Gaming, Complete) are generated programmatically in the backend using immutable definitions. They are not stored in `profiles.json`. When the UI requests the profile list, the backend concatenates the hardcoded defaults with the parsed custom profiles.
- **The Complete Profile**: Rather than mapping out steps manually, the executor will detect the "Complete" `profile_id` and explicitly invoke `RoutineService.executar()` to guarantee consistency.

## Concurrency and JobManager Integration
- The executor operates within a single thread spawned by `JobManager`.
- It acquires the `system_mutation` exclusive lock to prevent overlapping routines or manual optimizations during execution.
- Only the `JobManager` job ID is returned to the frontend. The frontend polls progress via `verificar_tarefa`.

## API Contracts (Frontend/Backend)
- **Frontend Request**: `window.Phoenix.executar_profile({profile_id: "uuid-1234"})`
- **Backend Response**: `{"job_id": "job-uuid"}`
- **Polling**: `window.Phoenix.verificar_tarefa("job-uuid")` returns `{ status: "running", progresso: 45, mensagem: "Limpando disco..." }`
- **No Remote Code Execution**: The API only accepts the string ID of the profile. Mapping to Python modules happens securely inside `ProfileExecutor`.

## File Placement Proposal
- `modules/core/profile_service.py` [NEW]
- `modules/core/profile_executor.py` [NEW]
- `modules/gui/api.py` [MODIFIED]
- `tests/test_profile_service.py` [NEW]
- `tests/test_profile_executor.py` [NEW]
- `gui/js/pages/page_routine_profiles.js` [NEW]
- `gui/js/operations/routine_executor.js` [MODIFIED/NEW]
