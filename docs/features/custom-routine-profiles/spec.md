# Custom Routine Profiles Specification

## Problem Statement
Technicians need to automate repetitive tasks based on specific scenarios (e.g., gaming setups, quick maintenance, deep cleaning). Currently, the "Complete Routine" is hardcoded and inflexible. Technicians waste time manually executing individual operations for cases that do not require the full routine, increasing the risk of skipping crucial steps like diagnostics and reports.

## Goals
- Allow technicians to create, edit, duplicate, and execute custom ordered sequences of existing operations.
- Provide sensible, immutable default profiles for common scenarios.
- Automatically manage Restore Points, diagnostics, and reports within the profile lifecycle.
- Maintain concurrency safety and ensure all execution occurs asynchronously in the backend.

## Non-Goals
- Cloud synchronization or sharing of profiles.
- Arbitrary scripts, custom PowerShell commands, or software removal capabilities.
- Parallel execution of multiple steps or profiles simultaneously.
- Complex per-step parameters (e.g., selecting specific registry keys to clean).
- Technician permission levels or external telemetry.

## User Personas and Workflow
**Primary Persona**: Computer Technician
**Workflow**: 
1. The technician accesses the "Routine Profiles" page.
2. Selects an existing Default Profile or creates a new Custom Profile from an allowlisted set of operations.
3. Clicks "Execute" on the chosen profile.
4. Tracks progress natively as the backend processes the sequence.
5. Reviews the generated report at the end of the execution.

## Default Profiles
These profiles are immutable, built-in, and cannot be deleted or edited.
1. **Quick Maintenance**: Initial diagnostic → Cleanup → Release standby memory → Final diagnostic → Report.
2. **Standard Maintenance**: Initial diagnostic → Cleanup → General optimization → Disk optimization → Final diagnostic → Report.
3. **Gaming**: Initial diagnostic → Cleanup → Gaming optimization → Release standby memory → Final diagnostic → Report.
4. **Complete**: Hardcoded to map exactly to the existing `RoutineService` behavior to ensure a single source of truth.

## Profile Data Fields
- `id`: string (UUID for custom, constant string for defaults).
- `name`: string (max 50 chars).
- `is_default`: boolean (true for built-in profiles).
- `steps`: array of strings (allowlisted step identifiers).
- `created_at`: timestamp.
- `updated_at`: timestamp.

## Profile Lifecycle and CRUD Behavior
- **List**: Retrieves all default and custom profiles combined.
- **View**: Displays profile details and steps.
- **Create**: Generates a new profile with a generated UUID.
- **Edit**: Updates a custom profile's name and step sequence. Fails if attempted on a default profile.
- **Duplicate**: Clones a default or custom profile into a new custom profile.
- **Delete**: Removes a custom profile. Fails if attempted on a default profile.
- **Restore Defaults**: Not applicable as defaults are dynamically injected and immutable; corrupted persistence files are overwritten with an empty custom list and safe defaults.

## Validation Rules
- **Profile Name**: Must be 1-50 characters, normalized (stripped of leading/trailing spaces). Duplicate names are rejected.
- **Empty Profiles**: Rejected. A profile must have at least one step.
- **Maximum Step Count**: Limited to 20 steps per profile to prevent abuse.
- **Unknown/Duplicate Steps**: Unknown step IDs are rejected. Duplicate steps are allowed unless structurally illogical (e.g., multiple reports).
- **Default Profile Protection**: Cannot be modified, deleted, or overwritten. Identifiers for defaults are reserved.
- **Report Restrictions**: A profile may contain at most *one* report step, which *must* be the final step.
- **Diagnostic Constraints**: If mutable operations exist, an initial diagnostic should ideally be the first step, and a final diagnostic should precede the report. (Enforced as a strong warning in UI, or strict backend validation depending on UX decision, but initially validated by backend: if report is requested, diagnostics must exist).
- **Restore Points**: Restore points are *not* exposed as a manually reorderable step. They are handled automatically by the executor policy.
- **Startup Analysis**: Treated as a non-mutable informational step.
- **Missing References**: If a requested profile ID does not exist, the backend aborts execution with a clear error.

## Execution Behavior
- **Asynchronous**: Execution is delegated to `JobManager`.
- **Concurrency**: Only one mutable profile can run at a time (locked via `exclusive_group="system_mutation"`).
- **Execution of Profiles Without Mutable Operations**: Permitted to run concurrently with other non-mutable reads, governed by `JobManager`.

## Progress Behavior
- The executor calculates progress proportionally `(current_step_index / total_steps) * 100`.
- The `JobManager.update_progress` method is called before each step begins.

## Restore-Point Behavior
- **Policy**: If the profile contains any step requiring a restore point (e.g., `optimize_general`, `optimize_gaming`, `optimize_disk`), the executor requests a restore point *once* before the first mutable step.
- **Session/In-Progress**: Reuses the existing application logic. If a restore point was already successfully created in the current session (or via "Option B" in the frontend before triggering the profile), the backend detects this state and skips redundancy.
- **Failure**: If restore point creation fails, the backend halts execution and returns a sanitized error (unless explicit continuation is implemented via frontend configuration, which is currently deferred).
- **Missing Privilege**: Handled by existing error codes (e.g., `NO_ADMIN`) and passed cleanly to the frontend.

## History and Report Behavior
- Executing a profile creates a standard session in `logs.py`.
- If the `report` step is included, it aggregates the `diagnostic_before` and `diagnostic_after` states and exports the standard TXT report.
- The history module transparently records the profile execution as a standard attendance log.

## Installed and Portable Behavior
- **Persistence Path**: Reuses `modules.shared.obter_pasta_base()` to ensure profiles are stored in `%PROGRAMDATA%\PhoenixOptimizer` (Installed) or the `dados/` folder (Portable).
- No mutable state is saved within the `gui/` directory or the read-only executable path.

## Recovery Behavior
- If `profiles.json` is corrupted, the backend creates a backup of the corrupted file (`profiles.corrupt.json`) and initializes a clean, empty list for custom profiles. Default profiles remain available.

## Acceptance Criteria
- [ ] Users can create, edit, duplicate, and delete custom profiles in the UI.
- [ ] Default profiles are visible but cannot be modified.
- [ ] Backend validates all profile structures (name length, valid steps, unique names).
- [ ] Execution runs asynchronously without freezing the pywebview window.
- [ ] The Complete Profile performs identically to the legacy Complete Routine.
- [ ] Restore points are generated automatically only when required by the operations.
- [ ] Profiles persist correctly in both Portable and Installed modes.
- [ ] Invalid execution requests return sanitized errors via `JobManager`.
