# Data Model & Interfaces: Redesign GUI + Spinner

## 1. Entities

Não há alterações nos modelos de dados persistidos em banco/arquivos para esta feature (além das melhorias de hardware implementadas em 011). No entanto, o controle de ciclo de vida assíncrono adiciona um modelo em memória principal:

### BackgroundJob (Dicionário em Memória - Backend)

Armazenado na variável global `_tarefas` do `gui_app.py`.

```json
{
  "status": "string", // "running", "done", "error"
  "resultado": "any", // Oculto se status="running", ou valor dict se "done", ou dict com erro se "error"
  "erro": "string"    // Preenchido apenas em caso de exceção nativa no backend
}
```

## 2. API JS/Python (pywebview)

Abaixo estão as assinaturas das 4 APIs adaptadas no backend para assincronismo (retornando job_id).

### `listar_inicializacao()`
**Retorna:** `{ "job_id": "uuid-v4-string" }`
**Resultado Esperado (após polling):** `{ "ok": true, "saida": "string" }`

### `listar_servicos()`
**Retorna:** `{ "job_id": "uuid-v4-string" }`
**Resultado Esperado (após polling):** `{ "ok": true, "servicos": [...] }`

### `obter_historico()`
**Retorna:** `{ "job_id": "uuid-v4-string" }`
**Resultado Esperado (após polling):** `{ "ok": true, "atendimentos": [...] }`

### `listar_backups_rollback()`
**Retorna:** `{ "job_id": "uuid-v4-string" }`
**Resultado Esperado (após polling):** `{ "ok": true, "backups": [...] }`

## 3. UI State (Frontend)

O frontend deverá expor um modelo de visualizações ("Slots" de Abas):
- `current_view`: ID da view atual ("dashboard", "hwmonitor", "cpuz", "otimizacoes", "logs").
- Ao transitar entre views, as divs com classe `view-slot` recebem `display: none` ou `display: block` de forma condicional, ou via CSS (ex: remoção/adição de classe `active`).
