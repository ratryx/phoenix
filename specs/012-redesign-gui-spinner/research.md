# Research: GUI Threading e Arquitetura de Layout

## 1. Auditoria de Métodos Bloqueantes (PhoenixAPI)

Avaliando o `modules/gui_app.py`, os seguintes métodos não utilizam `_iniciar_job` e, portanto, bloqueiam a thread principal do `pywebview` aguardando a resposta:

- `listar_inicializacao(self)`: Executa consulta WMI no PowerShell (`Get-CimInstance Win32_StartupCommand`). Essa chamada costuma levar 1-3 segundos, bloqueando completamente a UI.
- `listar_servicos(self)`: Executa `sc query state= all` que retorna centenas de serviços. Apesar de mais rápido que o WMI, ainda invoca um processo em subprocess e bloqueia o event loop JS, podendo causar engasgos no spinner.
- `obter_historico(self)`: Usa `glob` para ler e parsear múltiplos arquivos JSON de uma só vez na thread principal.
- `listar_backups_rollback(self)`: Mesma situação do histórico, lê todos os JSONs da pasta de backups de forma síncrona.

**Decisão**: Todos esses 4 métodos devem ser refatorados para usar `self._iniciar_job(lambda: ...)`, passando a retornar `job_id`. O frontend será ajustado para usar polling para essas ações, tal como já faz para `obter_diagnostico` e `executar_rotina_completa`.

## 2. Padrão Job ID e Polling no Frontend

O frontend (`gui/js/main.js` ou equivalente) deverá ter uma função padrão `async function awaitJob(jobId)` que encapsula o polling de 500ms via `setInterval` ou loops recursivos, atualizando a UI (exibindo o spinner) e só retornando o dado quando o status for `done`.
ZERO bloqueios, ZERO callbacks diretos síncronos longos.

## 3. Redesign da GUI: Slots (Abas)

**Decisão**: O layout do HTML atual precisará de uma Sidebar (lateral esquerda) com links `data-view="dashboard"`, `data-view="hwmonitor"`, etc. E uma div central `main-content` que receberá as "Views". As sessões para HWMonitor e CPU-Z estarão desabilitadas/com placeholder para futura implementação nas features 013 e 014.
