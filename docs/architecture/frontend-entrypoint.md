# Inventário do Entrypoint (`gui/app.js`)

## 1. Composition root / Bootstrap
* `bootstrap`: Inicializa a aplicação (sequência de carregamento).
* `registrarBotoesAcao`: Associa botões fixos aos métodos extraídos (diagnóstico, rotina completa).
* `aplicarQualidadeVisual`: Determina via bridge e aplica a classe no `document.body`.
* `aplicarNivelQualidade`: Aplica classes e gerencia chamadas de efeitos visuais.
* `gerarParticulas`: Renderiza visual estético baseado na qualidade.

## 2. Rotina Completa
* `executarRotinaCompleta`: Coordena a operação (proteção, feedback visual, await do job de backend, modal de erro, navegação e delegação para o Relatório).

## 3. Cliente e Sessão Portable
* `exibirSelecaoCliente`: Obtém a lista via pywebview e renderiza o painel customizado.
* `selecionarCliente`: Avisa o pywebview, manipula o header e a visibilidade da tela de seleção.
* `window.removerCliente`: Interage com modals de confirmação e avisa deleção ao backend.
* `window.confirmarNovoCliente`: Trata validação do input e encaminha para `selecionarCliente`.

## 4. Controles de Janela
* `registrarBotoesJanela`: Associa métodos nativos (`minimizar`, `fechar`) à `bridge.call`.
* `registrarDrag`: Inicia listener de arrastar na Titlebar e cabeçalhos.
* `processarMovimento` (interna a `registrarDrag`): Aplica o loop de `requestAnimationFrame` para `mover_janela`.

## 5. Sidebar / Router
* `carregarConteudoPagina`: O mapa de páginas / switch central do loader de conteúdo.
* `registrarSidebar`: Delega listeners do data-pagina para invocação do router.

## 6. Compatibilidade Global
* `corPorPercentual` (`Phoenix.ui.corPorPercentual`): Helper visual usado por outras páginas (sensores/hardware) para formatar badgets baseados em limite de porcentagem.

## 7. Código Morto
* Nenhum código estritamente morto detectado (funções órfãs). Todas são consumidas pelo bootstrap, botões nativos HTML ou router.

## 8. Responsabilidade Ambígua
* `aplicarNivelQualidade` e `gerarParticulas` tangenciam o bootstrap visual. Poderiam ir para um submódulo de "ui-visual" ou "effects", mas para não fragmentar em excesso (conforme restrição "Não crie módulos apenas para reduzir linhas"), serão mantidas no app.js como parte da aplicação/tema raiz da `window`.
