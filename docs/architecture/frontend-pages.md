# Frontend Pages Inventory (Pre-Extraction)

## Página Início
- **Funções Atuais**: `carregarHardwareInicial`, `atualizarRodapeFalha`, `atualizarCardsHardware`, `preencherRodapeHardware`, `iniciarAtualizacaoTempoReal`, `atualizarCardsTempoReal`
- **Chamadas à bridge**: `carregar_hardware_cache`, `obter_metricas_rapidas`
- **Estado lido**: Nenhum específico antes do cache.
- **Estado alterado**: `STATE.hardware`
- **IDs do DOM**: `texto-rodape`, `barra-progresso-rodape`, `cards-resumo-inicio`, `rodape-hardware`
- **Listeners**: Nenhum direto, atualizações são injetadas em tempo real.
- **Helpers**: `formatarBytes`, `corPorPercentual`
- **Intervalos**: `tempoReal` (3000ms)
- **Funções compartilhadas**: `formatters.js` será criado se `formatarBytes` e `corPorPercentual` forem usados por múltiplas páginas. `formatarBytes` e `corPorPercentual` são amplamente usados.
- **Globals necessários**: Nenhum extra.
- **Retorno esperado**: Promessas void.

## Página Diagnóstico
- **Funções Atuais**: `carregarDiagnostico`, `renderizarDiagnostico`
- **Chamadas à bridge**: `obter_diagnostico`
- **Estado lido**: Nenhum.
- **Estado alterado**: Nenhum global, apenas DOM local.
- **IDs do DOM**: `conteudo-diagnostico`, `secao-processos`
- **Listeners**: Navegação inline (onclicks do banner em `renderizarDiagnostico` usando `document.querySelector('.item-menu[data-pagina=\'otimizacao\']').click()` e scroll).
- **Helpers**: Nativos inline, `corBadge`, `textoBadge`, `corBarra`.
- **Intervalos**: Nenhum.
- **Funções compartilhadas**: Nenhuma.
- **Globals necessários**: `Phoenix.jobs.awaitJob`, `Phoenix.ui.feedback`.
- **Retorno esperado**: void.

## Página Hardware
- **Funções Atuais**: `carregarHardware`, `renderizarAbaHardware`
- **Chamadas à bridge**: `obter_info_sistema_detalhado`
- **Estado lido**: `STATE.dadosSistema`
- **Estado alterado**: `STATE.dadosSistema`
- **IDs do DOM**: `hw-conteudo`, `.hw-aba`
- **Listeners**: `.hw-aba` click listener (delegação ou attach inline em `carregarHardware`).
- **Helpers**: Nenhum.
- **Intervalos**: Nenhum.
- **Funções compartilhadas**: Nenhuma.
- **Globals necessários**: Nenhum.
- **Retorno esperado**: void.

## App.js Tamanho Atual
Aproximadamente 1651 linhas.
# Frontend Pages Inventory (Post-Extraction)

## Estrutura Criada
```text
gui/js/pages/
├── inicio.js
├── diagnostico.js
└── hardware.js
```

## Dependências Injetadas
- `Phoenix.pages.inicio.load()`
- `Phoenix.pages.diagnostico.load()`
- `Phoenix.pages.hardware.load()`

## Mudanças e Desacoplamento
- `app.js` exportou `corPorPercentual` para `window.corPorPercentual` como utilitário temporário compartilhado.
- `app.js` teve o seu event listener de atualização de diagnóstico alterado para chamar `Phoenix.pages.diagnostico.load()`.
- A manipulação do cache inicial e atualização em tempo real do dashboard foi encapsulada em `Phoenix.pages.inicio`.
- A lógica do diagnóstico, incluindo processamento de score e injeção do banner HTML, agora pertence unicamente a `diagnostico.js`.
- A aba de hardware, incluindo seus eventos de clique e re-renderização, foi internalizada no módulo `hardware.js`.

## Globais Exportados (Temporariamente)
- `window.corPorPercentual` - Utilizado por `inicio.js` e funções legadas de `app.js`.
- `window.renderizarAbaHardware` - Utilizado temporariamente como hook estático até a remoção completa de listeners inline no HTML.
