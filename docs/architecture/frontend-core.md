# Frontend Core Architecture

## Motivo da estratégia sem ES Modules
Para evitar problemas de CORS em arquivos locais carregados no WebView2/pywebview (file:// protocol), bem como evitar diferenças de escopo e problemas de empacotamento, adotamos o padrão de scripts clássicos encapsulados por IIFE com um único namespace (`window.Phoenix`).

## Tamanho do app.js
- **Tamanho Anterior:** ~1821 linhas
- **Tamanho Atual:** ~1651 linhas
O arquivo monolítico inicial teve suas funcionalidades de infraestrutura extraídas sem alterar renderizações ou eventos específicos de componentes, reduzindo e isolando falhas globais.

## Ordem de carregamento
1. `namespace.js` (Não possui dependências)
2. `state.js` (Depende de: `namespace`)
3. `bridge.js` (Depende de: `namespace`)
4. `feedback.js` (Depende de: `namespace`)
5. `jobs.js` (Depende de: `namespace`, `bridge`)
6. `lifecycle.js` (Depende de: `namespace`)
7. `router.js` (Depende de: `namespace`, `state`, `lifecycle`)
8. `app.js` (Depende de todos os anteriores)

## Namespace
A variável global `window.Phoenix` agrupa todos os módulos do projeto.

## Estado (`Phoenix.state`)
Objeto de dados compartilhados contendo configuração (ex: `nivelQualidadeVisual`), estado de navegação e timers (`intervalos`). É o source-of-truth mantido globalmente e consumido pelos módulos.

## Bridge (`Phoenix.bridge`)
Abstrai `window.pywebview.api`. Fornece um mecanismo seguro `whenReady()` que espera apenas uma vez o carregamento do pywebview, e `call(methodName, ...args)` que valida e encaminha chamadas para o backend Python.

## Jobs (`Phoenix.jobs`)
Fornece o sistema de polling com `awaitJob`. Trata nativamente estados "running", "done", "not_found" com delay de 500ms e limite de 120 tentativas (60s), resolvendo promessas com os resultados e rejeitando com erros amigáveis se algo falhar ou timeout ocorrer.
* Intervalo de Consulta: 500ms
* Tentativas Máximas: 120
* Timeout total: 60s
* Estados: 'running', 'done', 'not_found'

## Feedback (`Phoenix.ui.feedback`)
Extrai funções de UI genéricas do backend/frontend: `mostrarOverlay`, `atualizarOverlay`, `esconderOverlay`, e `confirmarModal`. Mantém a barra fina para leituras rápidas e card interativo para lógicas destrutivas.

## Lifecycle (`Phoenix.lifecycle`)
Centraliza os manipuladores assíncronos que precisam ser parados periodicamente (como `_sensoresInterval` e `STATE.intervalos.tempoReal`). O Router notifica automaticamente o gerenciador de ciclos no momento de leavePage().
- **Timers:** `tempoReal` (global, métricas gerais), `sensores` (HWMonitor, removido no exit da aba `hwmonitor`).
- **Política de Limpeza:** `clearInterval()` por nome. Sair da aba 'hwmonitor' desliga o timer de nome 'sensores'.

## Router (`Phoenix.router`)
Lida com a transição entre abas (escondendo e exibindo divs). Invoca o loader da página através de hooks `Phoenix.app.loadPage` (ou repassa callback). Cuida também da integração com lifecycle para limpar intervalos ao sair das telas.
- **Páginas Conhecidas:** `inicio`, `diagnostico`, `hardware`, `limpeza`, `otimizacao`, `servicos`, `historico`, `hwmonitor`, `relatorio`.

## Bootstrap (`app.js`)
Arquivo principal com as lógicas ativas de cada página. Possui proteção estrita contra inicialização dupla (`let bootstrapStarted = false`).

## Tratamento de erros e limitações
- Timeout ou não-disponibilidade da bridge rejeitam promises imediatamente; os callbacks da interface DOM continuam falhando silenciosamente no modo polling.
- Interface construída com strings DOM (`innerHTML`), suscetível a bugs visuais caso `state` e DOM desalinhem.

## Globais Temporários
Por questões de dependência reversa no HTML legado (funções no `onclick` de botões HTML inline), as seguintes funções/globais foram mantidas temporariamente apontando pros módulos do Phoenix:
* `window.mostrarOverlay` - Necessário pra hooks e HTML.
* `window.esconderOverlay` - Necessário pra hooks e HTML.
* `window.awaitJob` - Manutenção de retrocompatibilidade temporária no app.
* `window.irParaPagina` - Usado inline em `onclick`.
* `window.removerCliente` - Usado inline em `onclick` do HTML dinâmico portátil.
* `window.selecionarCliente` - Usado inline em `onclick` do HTML dinâmico portátil.
* `window.confirmarNovoCliente` - Usado inline em `onclick` no HTML fixo portátil.

## Smoke Test Manual
O smoke test manual de comportamento não pôde ser verificado, ambiente CI não possui display. Encontra-se "Pendente".
