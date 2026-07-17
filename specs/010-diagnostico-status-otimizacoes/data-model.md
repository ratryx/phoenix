# Phase 1: Data Model

## Entidades Principais

### StatusOtimizacao

Representa o status atual verificado de um item de otimização específico.

```json
{
  "id": "string",            // Identificador interno, ex: "plano_energia"
  "descricao": "string",     // Descrição amigável, ex: "Plano de energia"
  "ativo": "boolean",        // true = otimizado (verde), false = inativo (vermelho)
  "detalhe": "string"        // Texto extra, ex: "Está em Equilibrado ao invés de Alto Desempenho"
}
```

### DiagnosticoResultado

Agrupa os status verificados de todas as otimizações.

```json
{
  "data_verificacao": "string", // ISO-8601
  "total_ativos": "number",
  "total_inativos": "number",
  "itens": [
    // Lista de StatusOtimizacao
  ]
}
```

### CacheHardware

Registra as informações capturadas no scan.

```json
{
  "data_scan": "string",
  "validacao": {
    "cpu_modelo": "string",
    "ram_total_gb": "number",
    "gpus": ["string"]
  },
  "dados": {
    // Mesma estrutura retornada atualmente pelo module hardware.py
  }
}
```
