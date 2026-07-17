# Frontend Core & Globals

A camada core do Phoenix Optimizer encapsula a lógica estrutural, delegando integrações e gerenciando o ciclo de vida. Toda lógica baseia-se em namespaces IIFE, dispensando ES Modules e garantindo compatibilidade direta.

## Estrutura de Diretórios e Módulos
- `gui/js/core/`
  - `namespace.js`: Inicializa o objeto `window.Phoenix` e as propriedades básicas do ecossistema.
  - `state.js`: Configura `Phoenix.state`, definindo `paginaAtual`, `hardware`, `dadosSistema` e flags globais.
  - `bridge.js`: Wrapper robusto para `window.pywebview.api`, implementando promises retentivas e timeouts para `call()` e `whenReady()`.
  - `jobs.js`: Encapsula o polling para `Phoenix.jobs.awaitJob`, verificando o andamento de operações de backend até completude, erro ou timeout.
  - `lifecycle.js`: Gerenciamento de eventos baseados em tempo de tela (timers `setInterval` e timeouts limitados ao contexto de visibilidade da página), efetuando teardown automático em transições de rotas.
  - `router.js`: Roteamento simplificado, atualizando a Sidebar, resolvendo fallback de Hash, atualizando `window.location.hash`, controlando transição visual `.ativa` e delegando conteúdo via `_pageLoader`.

## Integração Adicional (UI, Features, Operations)
- `gui/js/features/client-session.js`: Mantém estados e endpoints do histórico unificado do cliente portable.
- `gui/js/operations/`: Funções exclusivas que controlam fluxos maiores com múltiplas interações inter-processos e proteção de concorrência (`routine.js` e `restore-point.js`).
- `gui/js/ui/`: Ferramentas visuais reaproveitáveis que controlam propriedades globais (`window-controls.js` para manipulação de janelas no frameless, e `feedback.js` para os overlays bloqueantes e custom alerts).
