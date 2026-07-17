# Frontend Core Architecture

## Motivo da estratégia sem ES Modules
Para evitar problemas de CORS em arquivos locais carregados no WebView2/pywebview (file:// protocol), bem como evitar diferenças de escopo e problemas de empacotamento, adotamos o padrão de scripts clássicos encapsulados por IIFE com um único namespace (`window.Phoenix`).

## Ordem de carregamento
1. `namespace.js`
2. `state.js`
3. `bridge.js`
4. `feedback.js`
5. `jobs.js`
6. `lifecycle.js`
7. `router.js`
8. `app.js`

## Namespace
A variável global `window.Phoenix` agrupa todos os módulos do projeto.

## Estado (`Phoenix.state`)
Objeto de dados compartilhados contendo configuração (ex: `nivelQualidadeVisual`), estado de navegação e timers (`intervalos`). É o source-of-truth mantido globalmente e consumido pelos módulos.

## Bridge (`Phoenix.bridge`)
Abstrai `window.pywebview.api`. Fornece um mecanismo seguro `whenReady()` que espera apenas uma vez o carregamento do pywebview, e `call(methodName, ...args)` que valida e encaminha chamadas para o backend Python.

## Jobs (`Phoenix.jobs`)
Fornece o sistema de polling com `awaitJob`. Trata nativamente estados "running", "done", "not_found" com delay de 500ms e limite de 60s, resolvendo promessas com os resultados e rejeitando com erros amigáveis se algo falhar ou timeout ocorrer.

## Feedback (`Phoenix.ui.feedback`)
Extrai funções de UI genéricas do backend/frontend: `mostrarOverlay`, `atualizarOverlay`, `esconderOverlay`, e `confirmarModal`. Mantém a barra fina para leituras rápidas e card interativo para lógicas destrutivas.

## Lifecycle (`Phoenix.lifecycle`)
Centraliza os manipuladores assíncronos que precisam ser parados periodicamente (como `_sensoresInterval` e `STATE.intervalos.tempoReal`). 

## Router (`Phoenix.router`)
Lida com a transição entre abas (escondendo e exibindo divs). Invoca o loader da página através de hooks `Phoenix.app.loadPage` (ou repassa callback). Cuida também da integração com lifecycle para limpar intervalos ao sair das telas.

## Bootstrap (`app.js`)
Arquivo principal com as lógicas ativas de cada página (diagnostico, limpeza, etc). Mantém o handler `pywebviewready` mas delegando pra `Phoenix.bridge.whenReady()`. Protege a inicialização múltipla.

## Globais Temporários
Por questões de dependência reversa no HTML legado (funções no `onclick` de botões HTML inline), as seguintes funções/globais foram mantidas temporariamente apontando pros módulos do Phoenix:
* `window.mostrarOverlay`
* `window.esconderOverlay`
* `window.awaitJob`
* `window.irParaPagina`
* `window.removerCliente`
* `window.selecionarCliente`
* `window.confirmarNovoCliente`

## Limitações
A interface DOM continua imperativa usando concatenação de strings (HTML templating primitivo). O CSS segue sem escopo forte.
Erros periódicos não enviam popups intrusivos e continuam silenciosos no modo polling por timer (ex: atualizar stats não desliga a dashboard no primeiro erro, ele só tenta novamente no próximo ciclo de 3s).

## Próximos módulos a extrair
- Páginas individuais: `hardware.js`, `diagnostico.js`, `limpeza.js`, `otimizacao.js`, `servicos.js`, `historico.js`, `sensores.js`.
