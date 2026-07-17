# Phase 0: Research & Decisions

## Context

Este documento consolida as decisões técnicas necessárias para implementar as features 010 (Diagnóstico de Status) e 011 (Cache de Hardware), considerando o timeout de 5 segundos e a obrigatoriedade de não bloquear a GUI (Feature 012).

## Research Items

### 1. Consulta ao Windows para Status de Otimização (010)

Precisamos consultar o estado de chaves de registro e serviços de forma performática.

- **Decision**: Utilizar `powershell` com `Get-ItemProperty` e `Get-Service` para consultas em lote sempre que possível, para minimizar o overhead de instanciar processos subprocess.run. 
- **Rationale**: Chamar `subprocess.run` para cada chave de registro individualmente pode ser lento. Uma alternativa é montar um script PowerShell de uma linha que consulta múltiplas chaves e retorna um JSON unificado. No entanto, o `wmi` e `psutil` podem ser usados quando mais eficientes.
- **Alternatives considered**: Utilizar o módulo `winreg` nativo do Python. **Decision Altered**: Sim, usar `winreg` é ordens de magnitude mais rápido que invocar `powershell`. Usaremos `winreg` para leitura de registro e `subprocess` apenas para `powercfg` e serviços (`sc query`).

### 2. Implementação do Cache de Hardware (011)

Precisamos salvar e invalidar cache rapidamente.

- **Decision**: Salvar dados em um arquivo JSON. Na inicialização, realizar uma leitura rápida via `psutil` (RAM) e `wmi` (CPU e GPU básica) para validar o cache.
- **Rationale**: A leitura do WMI e psutil para métricas básicas é rápida (< 0.5s). Apenas se houver divergência, dispara o scan completo (que inclui leitura S.M.A.R.T, etc., que demora mais).
- **Alternatives considered**: Guardar no registro. Não é seguro e contraria a filosofia de não poluir o sistema. JSON em `%PROGRAMDATA%` é a melhor escolha.

### 3. Integração com Padrão Job ID (012)

- **Decision**: A arquitetura de `gui_app.py` será estruturada para alocar as requisições de frontend em threads usando o método `_iniciar_job` já esboçado na feature 012. 
- **Rationale**: Garante responsividade. Como a comunicação pywebview bloqueia, a resposta imediata de um ID e um polling (via setTimeout do JS) mantém o frontend livre.
