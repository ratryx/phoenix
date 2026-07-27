# Portable Client Security Model

This document outlines the security architecture and contracts implemented to protect data bounds and prevent Cross-Site Scripting (XSS) in the Portable Mode Client Selection workflow.

## 1. Stable Client ID vs. Display Name
The system maintains a strict separation between the backend-controlled filesystem path identifier and the user-controlled display name.
- **Client ID (`id`)**: A slugified version of the input, stripped of accents and spaces, appended with a unique UUID prefix (e.g., `joao-silva-a1b2c3d4`). This is used exclusively for storage directories.
- **Display Name (`nome_display`)**: The raw, unescaped string entered by the user. It is preserved identically to support arbitrary unicode and symbols.

## 2. Canonical Portable Client Root
All portable data is stored within the `dados/clientes/` directory relative to the executable path. A rigorous containment verification is enforced on any directory interaction:
1. Validates the client ID against reserved Windows names (`CON`, `PRN`, `AUX`, etc.) and path separators (`/`, `\`, `..`).
2. Verifies that the resolved absolute path of the target directory is strictly a child of the canonical `dados/clientes/` absolute root.
3. Explicitly rejects actions on the root directory itself.

## 3. Junction and Symlink Rejection
To prevent directory traversal and arbitrary file deletion through malicious links, the backend explicitly rejects symlinks (`.is_symlink()`) and Windows directory junctions (`os.path.isjunction()`).

## 4. Legacy Compatibility
Folders created prior to the ID/Name separation are safely recognized as legacy clients if they are direct children of the canonical root and meet the strict string validation rules.
- Legacy folders without a `meta.json` are assigned their exact folder name as their ID.
- Legacy clients are never destructively renamed.

## 5. Deletion Boundaries
Deletion strictly requires Portable Mode. The endpoint refuses any deletion requests against missing clients, malformed IDs, absolute paths, or paths breaking containment. Only the backend ID may be passed.

## 6. Atomic `meta.json` Writes
Writing metadata (`meta.json`) uses an atomic strategy:
- Writes to a temporary file (`mkstemp`).
- Flushes and forces a disk sync (`os.fsync`).
- Atomically replaces the old file using `os.replace`.
- If a write fails, the original data remains intact, returning `PERSISTENCE_WRITE_FAILED`.

## 7. API Error Codes
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

## 8. Frontend Text-Only Rendering
All UI updates for the portable client session operate using strict DOM generation APIs (`document.createElement`, `textContent`) instead of `innerHTML`. This mitigates XSS by ensuring that malicious display names (e.g., `<script>alert(1)</script>`) are rendered purely as text nodes. Inline events (`onclick`, `onkeydown`) have been eliminated in favor of dynamically bound event listeners.

## 9. Remaining Unverified Behavior & Risks
- **Real Windows Junction Behavior**: While `os.path.isjunction()` is implemented and verified through mocks, real-world creation of junctions for test automation was skipped due to administrative privilege limitations in standard CI environments. This requires controlled manual validation.
- **XSS Risks Outside Selector**: The mitigation strategy was explicitly applied to the Portable Client Selection screen. If user-controlled client names leak into historical reports or logs rendered with unsafe string templates later in the application flow, XSS remains a risk there. Those boundaries remain out of scope for this specific task.
