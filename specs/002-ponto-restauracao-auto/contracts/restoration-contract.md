# JavaScript/Python Contract: Ponto de Restauração

This document outlines the API contracts and state interactions between the UI layers (CLI and GUI) and the core optimization module for restore point operations.

## Python Core Interface (`modules/otimizacao.py`)

### 1. `criar_ponto_restauracao()`
Executes the creation of a Windows System Restore point.
*   **Parameters**: None
*   **Returns**:
    ```json
    {
      "ok": true,
      "mensagem": "Ponto de restauração 'Phoenix Optimizer - Pré-Otimização' criado com sucesso."
    }
    ```
    Or on failure:
    ```json
    {
      "ok": false,
      "erro": "A Restauração do Sistema está desativada no Windows.",
      "codigo": "RESTORE_DISABLED" | "LIMIT_EXCEEDED" | "NO_ADMIN" | "UNKNOWN"
    }
    ```

---

## Python GUI Bridge Interface (`modules/gui_app.py`)

The JS frontend invokes these methods in sequence to allow rendering beautiful custom UI modals.

### 1. `criar_ponto_restauracao()`
Direct wrapper of the core module function to be called by JS.

### 2. `executar_otimizacao_geral_confirmada()`
Applies the general optimizations. Must be called after the restore point check/prompt is completed.
*   **Parameters**: None
*   **Returns**: `{"ok": true}` or `{"ok": false, "erro": "string"}`

### 3. `executar_otimizacao_gaming_confirmada(resetar_rede: bool)`
Applies gaming optimizations. Must be called after the restore point check/prompt is completed.
*   **Parameters**: `resetar_rede` (bool)
*   **Returns**: `{"ok": true}` or `{"ok": false, "erro": "string"}`

---

## GUI Frontend Sequence Flow (JS)

For any optimization action (e.g., clicking "Otimização Geral" or "Otimização para Jogos"):

1.  **Frontend State**: Show loading overlay: `"Criando ponto de restauração do sistema..."`.
2.  **API Call**: `const res = await chamarAPI("criar_ponto_restauracao")`.
3.  **Outcome Handling**:
    *   **If `res.ok === true`**:
        *   Frontend shows a confirmation modal: *"Ponto de restauração criado com sucesso! Deseja prosseguir com as otimizações?"*
        *   If confirmed, call `executar_otimizacao_..._confirmada()`.
        *   If cancelled, close modal and show safe cancel status.
    *   **If `res.ok === false`**:
        *   Frontend shows warning modal: *"Atenção: A criação do ponto de restauração falhou ({res.erro}). Deseja prosseguir com as otimizações mesmo assim?"*
        *   If confirmed, call `executar_otimizacao_..._confirmada()`.
        *   If cancelled, close modal and show safe cancel status.
