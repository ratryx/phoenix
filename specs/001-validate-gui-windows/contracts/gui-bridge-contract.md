# GUI Bridge JavaScript/Python Contract

The GUI application uses `pywebview` to bridge the HTML/JS frontend and the Python backend. The frontend invokes Python methods asynchronously via the global `window.pywebview.api` object.

## Python API Interface (`PhoenixAPI`)

All backend bridge methods return JSON-compatible structures (dictionaries, lists, strings) which are automatically serialized by `pywebview`.

### 1. `obter_hardware()`
* **Parameters**: None
* **Returns**:
  ```json
  {
    "cpu": {
      "nome": "string",
      "nucleos_fisicos": 4,
      "nucleos_logicos": 8,
      "frequencia_mhz": 3200
    },
    "ram": {
      "total_gb": 16
    },
    "gpus": [
      {
        "nome": "string",
        "fabricante": "string",
        "vram_gb": 8
      }
    ]
  }
  ```

### 2. `obter_nivel_qualidade_visual()`
* **Parameters**: None
* **Returns**: `"alto" | "medio" | "baixo"`

### 3. `iniciar_atendimento(nome_cliente: str)`
* **Parameters**:
  * `nome_cliente` (string, optional)
* **Returns**:
  ```json
  {
    "id_atendimento": "string"
  }
  ```

### 4. `obter_diagnostico()`
* **Parameters**: None
* **Returns**:
  ```json
  {
    "ok": true,
    "dados": {
      "cpu_uso": 12.5,
      "ram_uso_percentual": 45.2,
      "discos": [
        {
          "letra": "C:",
          "total_gb": 500,
          "livre_gb": 220
        }
      ]
    }
  }
  ```
  Or if error:
  ```json
  {
    "ok": false,
    "erro": "string"
  }
  ```

### 5. `executar_limpeza()`
* **Parameters**: None
* **Returns**:
  ```json
  {
    "ok": true,
    "espaco_liberado_mb": 1024.5
  }
  ```

### 6. `executar_otimizacao_geral()`
* **Parameters**: None
* **Returns**:
  ```json
  {
    "ok": true
  }
  ```

### 7. `executar_otimizacao_gaming(resetar_rede: bool)`
* **Parameters**:
  * `resetar_rede` (boolean)
* **Returns**:
  ```json
  {
    "ok": true
  }
  ```

### 8. `otimizar_disco()`
* **Parameters**: None
* **Returns**:
  ```json
  {
    "ok": true,
    "saida": "string"
  }
  ```

### 9. `listar_inicializacao()`
* **Parameters**: None
* **Returns**:
  ```json
  {
    "ok": true,
    "saida": "string"
  }
  ```

### 10. `listar_servicos()`
* **Parameters**: None
* **Returns**:
  ```json
  {
    "ok": true,
    "servicos": [
      {
        "nome": "string",
        "status": "running | stopped",
        "exibicao": "string"
      }
    ]
  }
  ```

### 11. `desativar_servico(nome_servico: str)`
* **Parameters**:
  * `nome_servico` (string)
* **Returns**:
  ```json
  {
    "ok": true
  }
  ```

### 12. `ativar_servico(nome_servico: str)`
* **Parameters**:
  * `nome_servico` (string)
* **Returns**:
  ```json
  {
    "ok": true
  }
  ```

### 13. `obter_historico()`
* **Parameters**: None
* **Returns**:
  ```json
  {
    "ok": true,
    "atendimentos": []
  }
  ```

### 14. `executar_rotina_completa(nome_cliente: str)`
* **Parameters**:
  * `nome_cliente` (string)
* **Returns**:
  ```json
  {
    "ok": true,
    "id_atendimento": "string",
    "antes": {},
    "depois": {},
    "espaco_liberado_mb": 1024.5,
    "relatorio_txt": "string"
  }
  ```

### 15. `minimizar_janela()`
* **Parameters**: None
* **Returns**: None (void)

### 16. `fechar_janela()`
* **Parameters**: None
* **Returns**: None (void)
