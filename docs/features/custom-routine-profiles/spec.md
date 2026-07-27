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
- Complex per-step parameters.
- Technician permission levels or external telemetry.

## Profile Ownership
Routine profiles are **application-wide**. They are shared across all clients and attendances in the current installation or portable drive.

## User Workflow
1. The technician accesses the "Routine Profiles" page.
2. Selects an existing Default Profile or creates a Custom Profile from an allowlisted set of operations.
3. Clicks "Execute".
4. Tracks progress natively as the backend processes the sequence.
5. Reviews the generated report in the History tab.

## Default Profiles
Default profiles have stable string identifiers and are immutable.
1. `default-quick` (Quick Maintenance): `[diagnostic_before, cleanup, standby_memory, diagnostic_after, report]`
2. `default-standard` (Standard Maintenance): `[diagnostic_before, cleanup, optimize_general, optimize_disk, diagnostic_after, report]`
3. `default-gaming` (Gaming): `[diagnostic_before, cleanup, optimize_gaming, standby_memory, diagnostic_after, report]`
4. `default-complete` (Complete): `[diagnostic_before, cleanup, optimize_general, diagnostic_after, report]`

## Profile Schema
- `id`: string (UUID4 for custom, e.g. `default-quick` for defaults).
- `name`: string (max 50 chars).
- `is_default`: boolean.
- `steps`: array of string identifiers from the step allowlist.

## Profile Lifecycle and CRUD Behavior
- **List**: Combines hardcoded defaults and parsed custom profiles.
- **View**: Displays details and steps.
- **Create**: Generates a new profile with a UUID. Names must be 1-50 chars, stripped of leading/trailing spaces. Duplicate names (case-insensitive) are rejected.
- **Edit**: Updates a custom profile. Updating a default ID returns an error.
- **Duplicate**: Clones any profile into a new custom UUID, prepending "Copy of " to the name.
- **Delete**: Removes a custom profile.
- **Unknown ID**: Returning `PROFILE_NOT_FOUND`.
- **Reserved ID**: Custom profiles cannot use the `default-` prefix.

## Validation Rules
- **Empty Profiles**: Rejected.
- **Maximum Steps**: 20 steps max.
- **Unknown Steps**: Rejected.
- **Duplicate Steps**: Permitted structurally, except for `report`.
- **Report Rule**: Maximum of *one* `report` step allowed, and it *must* be the final step of the profile. If included, the profile should logically include `diagnostic_before` and `diagnostic_after` for correct aggregation.

## Step Metadata
Every step uses fixed backend logic. No PowerShell text is accepted from the frontend.
- `diagnostic_before`: `mutates: false, requires_rp: false, admin: false, report: produces snapshot_antes`
- `cleanup`: `mutates: true, requires_rp: false, admin: true, report: produces espaco_liberado_mb`
- `optimize_general`: `mutates: true, requires_rp: true, admin: true, report: none`
- `optimize_gaming`: `mutates: true, requires_rp: true, admin: true, report: none`
- `optimize_disk`: `mutates: true, requires_rp: false, admin: true, report: none`
- `standby_memory`: `mutates: true, requires_rp: false, admin: true, report: none`
- `startup_analysis`: `mutates: false, requires_rp: false, admin: false, report: none`
- `diagnostic_after`: `mutates: false, requires_rp: false, admin: false, report: produces snapshot_depois`
- `report`: `mutates: false, requires_rp: false, admin: false, report: consumes snapshots and space`

## Execution Behavior
- Profile execution creates an asynchronous job using `JobManager`.
- Only one mutating profile can run at a time (locked by `system_mutation`).
- **Progress Contract**: Backend sends `{"status": "running", "progresso": N, "mensagem": "..."}`. Progress is calculated deterministically `(current_step_index / total_steps) * 100`.

## Restore-Point Behavior
- **Policy**: The executor inspects the sequence. Immediately before the *first* step where `requires_rp` is true, it requests a Restore Point.
- If previous steps (e.g. `diagnostic_before`) do not require one, they run first.
- **Option B Flow (Frontend Sync)**:
  - If the Restore Point fails, the job immediately halts and returns a sanitized error `RESTORE_POINT_FAILED`.
  - The frontend catches this and displays the legacy "Continuar mesmo assim" modal.
  - If the user confirms, the frontend invokes the profile execution again, passing a new parameter: `executar_profile(profile_id, { skip_restore_point: true })`.
  - The executor restarts the profile, skipping the Restore Point check entirely.

## Report and History Contracts
- Execution automatically relies on the active attendance (`id_atendimento`). If none exists, the executor must create a new attendance session via `logs.gerar_id_atendimento()`.
- The `diagnostic_before` step invokes `logs.salvar_snapshot(..., "antes")`.
- The `cleanup` step tracks returned space.
- The `diagnostic_after` step invokes `logs.salvar_snapshot(..., "depois")`.
- The `report` step requires these snapshots to generate the TXT format. If a profile omits cleanup, space is `0`. If it omits diagnostics, the report gracefully outputs empty sections.

## Persistence and Errors
- **Paths**: Saved in `%PROGRAMDATA%\PhoenixOptimizer\profiles.json` (Installed) or `dados/profiles.json` (Portable).
- **Read-Only Environments**: If the portable drive is read-only, saving returns a sanitized error `PORTABLE_DRIVE_READONLY`.
- **Sanitized Errors**: No tracebacks, system paths, or module names are leaked. Errors return clean messages (e.g., "Operação falhou").
