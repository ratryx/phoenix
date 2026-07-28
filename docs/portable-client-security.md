# Portable Client Security Model

This document outlines the security architecture and contracts implemented to protect data bounds and prevent Cross-Site Scripting (XSS) in the Portable Mode Client Selection workflow.

## 1. Stable Client ID vs. Display Name
The system maintains a strict separation between the backend-controlled filesystem path identifier and the user-controlled display name.
- **Client ID (`id`)**: A slugified version of the input, stripped of accents and spaces, appended with a unique UUID prefix (e.g., `joao-silva-a1b2c3d4`). This is used exclusively for storage directories.
- **Display Name (`nome_display`)**: The raw, unescaped string entered by the user. It is preserved identically to support arbitrary unicode and symbols.

## 2. Canonical Portable Client Root
All portable data is stored within the `dados/clientes/` directory relative to the executable path. A rigorous containment verification is enforced on any directory interaction:
1. Validates the client ID with a strict format: lowercase ASCII, digits, hyphens, and underscores only (`^[a-z0-9_-]{1,100}$`). This explicitly rejects reserved Windows names, separators, quotes, spaces, dots, and traversal characters.
2. Performs **two-phase path validation** (lexical then resolved). Raw and resolved paths serve different validation purposes.
3. Lexical Phase: Validates that the raw candidate path is a direct child of the raw root. Rejects the root itself.
4. Link Checks: Rejects the path if it is a symlink (`.is_symlink()`) or a junction (`os.path.isjunction()`). These lexical link checks happen before resolution to prevent alias attacks where a link outside the root resolves to a valid inside target.
5. Resolution Phase: Resolves both root and candidate to their absolute paths and verifies component-aware containment (`candidate.is_relative_to(root)`).

## 3. Collision Retries & Immediate Deletion Revalidation
- **Collision Resistance**: Client IDs are appended with an 8-character UUID. If an ID collides, the system will retry up to 5 times. If exhaustion occurs, creation fails safely without modifying any existing data.
- **Immediate Deletion Revalidation**: Deletion strictly re-runs the entire two-phase path validation (ID checks, link checks, raw vs resolved containment) immediately before invoking `shutil.rmtree()`. This mitigates TOCTOU (Time-Of-Check to Time-Of-Use) attacks where an attacker replaces a directory with a symlink right before deletion.

## 4. Legacy Compatibility
Folders created prior to the ID/Name separation are safely recognized as legacy clients if they are direct children of the canonical root and meet the strict string validation rules.
- Legacy folders without a `meta.json` are assigned their exact folder name as their ID.
- Legacy clients are never destructively renamed.

## 5. Authoritative Identity vs Metadata ID
The validated direct-child directory name is ALWAYS the authoritative client ID.
- The `id` property stored in `meta.json` never controls paths, selection, deletion, or logging.
- If `meta.json.id` differs from the physical directory name, the physical directory name remains the authoritative ID, a sanitized local warning is recorded, and the backend continues using the safe directory name.
- If the metadata ID is missing or contains traversal/invalid characters, the system still relies purely on the physical directory name as the authoritative ID.

## 6. Deletion Boundaries
Deletion strictly requires Portable Mode. The endpoint refuses any deletion requests against missing clients, malformed IDs, absolute paths, or paths breaking containment. Only the backend ID may be passed. Immediate TOCTOU revalidation ensures safe deletion.

## 7. Atomic `meta.json` Writes & Selection Rollback
Writing metadata (`meta.json`) uses an atomic strategy:
- Writes to a temporary file (`mkstemp`).
- Flushes and forces a disk sync (`os.fsync`).
- Atomically replaces the old file using `os.replace`.
- If a write fails during client creation, the newly created empty candidate directory is safely removed to prevent leaving a visible orphan client. Pre-existing directories are never deleted upon write failure.
- Client selection explicitly persists required metadata atomically *before* setting the active in-memory client state. If persistence fails, the selection is aborted, returning `PERSISTENCE_WRITE_FAILED`, and the active memory state remains entirely unchanged (rolled back to previous).
- **Durable Metadata Only**: `meta.json` explicitly only stores durable domain properties (ID, name, timestamps). Transport properties (like `ok` or error codes) are never persisted to disk.

## 8. API Error Codes
The API bridge enforces a stable, sanitized error contract. Tracebacks, exceptions, absolute paths, and user data are never leaked in error messages.
Supported codes:
- `INVALID_CLIENT_NAME`
- `INVALID_CLIENT_ID`
- `CLIENT_NOT_FOUND`
- `CLIENT_DELETE_FAILED`
- `CLIENT_DELETE_FAILED_PERMISSION`
- `CLIENT_SELECT_FAILED`
- `PORTABLE_MODE_REQUIRED`
- `PERSISTENCE_WRITE_FAILED`
- `CLIENT_CREATE_FAILED`
- `UNKNOWN_ERROR` (Fallback for unexpected exceptions without leaking untrusted backend codes or tracebacks)

## 9. Frontend Text-Only Rendering
All UI updates for the portable client session operate using strict DOM generation APIs (`document.createElement`, `textContent`) instead of `innerHTML`. This mitigates XSS by ensuring that malicious display names (e.g., `<script>alert(1)</script>`) are rendered purely as text nodes. Inline events (`onclick`, `onkeydown`) have been eliminated in favor of dynamically bound event listeners.

## 10. CLI and Launcher Test Coverage
Extensive regression tests validate the CLI menus, portable launcher flows, domain ID collisions, and TOCTOU vulnerabilities natively.

## 11. Remaining Unverified Behavior & Risks
- **Real Windows Junction Behavior**: While `os.path.isjunction()` is implemented and verified through mocks, real-world creation of junctions for test automation was skipped due to administrative privilege limitations in standard CI environments. This requires controlled manual validation.
- **XSS Risks Outside Selector**: The mitigation strategy was explicitly applied to the Portable Client Selection screen. If user-controlled client names leak into historical reports or logs rendered with unsafe string templates later in the application flow, XSS remains a risk there. Those boundaries remain out of scope for this specific task.
