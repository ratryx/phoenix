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

## Hardware (`gui/js/pages/hardware.js`)

**Rota:** `hardware`
**Namespace:** `Phoenix.pages.hardware`

### Funções
- `load()`: Delega para `carregarHardware()`.
- `carregarHardware()`: Associa eventos de abas se não existirem, aciona a bridge `obter_info_sistema_detalhado`, salva dados em `Phoenix.state.dadosSistema` e renderiza a aba CPU.
- `renderTab(aba)`: Responsável por injetar o HTML dinâmico com base na aba (`cpu`, `gpu`, `memoria`, `sistema`, `discos`).

### Compatibilidade
- Exporta temporariamente `window.renderizarAbaHardware` para lidar com os cliques das abas que ainda estão hardcoded.

## Sensores / HWMonitor (`gui/js/pages/sensores.js`)

**Rota:** `hwmonitor`
**Namespace:** `Phoenix.pages.hwmonitor`

### Endpoint Utilizado
- `obter_metricas_completas`
- **Payload Esperado:** `{ok: true, cpu: {total, freq_mhz, por_nucleo}, ram: {percent, usada_gb, disponivel_gb}, gpu: {uso, temp, vram_usada, vram_total}, disco: {leitura_mb, escrita_mb}}`

### Comportamento
- **Entrada:** `load()` e `enter()` renderizam a estrutura base e realizam uma primeira atualização imediata, registrando também o polling no `Phoenix.lifecycle` sob a chave `sensores`.
- **Polling:** A cada 3000 ms. Há proteção contra sobreposição de requisições travando a flag `atualizando`.
- **Saída:** O `lifecycle.leavePage("hwmonitor")` é chamado indiretamente pelo router, limpando o timer.
- **Erro:** Falhas na requisição do endpoint são tratadas no catch e a flag é limpa silenciosamente.
- **Fallbacks:** Renderiza fallback se temperatura não suportada. Trata a ausência de `%`.
- **IDs do DOM:** `hw-cpu-total`, `hw-cpu-bar`, `hw-cpu-freq`, `hw-nucleos`, `hw-ram-pct`, `hw-ram-bar`, `hw-ram-usada`, `hw-ram-livre`, `hw-gpu-nome`, `hw-gpu-uso`, `hw-gpu-bar`, `hw-gpu-temp`, `hw-gpu-vram`, `hw-disk-read`, `hw-disk-write`.
- **Estado:** Utiliza `Phoenix.state.hardware` e `Phoenix.state.paginaAtual`.
- **Helpers:** Utiliza `Phoenix.ui.corPorPercentual` para barras.

- **Intervalos**: Nenhum.
- **Funções compartilhadas**: Nenhuma.
- **Globals necessários**: Nenhum.
- **Retorno esperado**: void.

## Limpeza (`gui/js/pages/limpeza.js`)

**Rota:** `limpeza`
**Namespace:** `Phoenix.pages.limpeza`

### Funções
- `load()`: Adiciona event listener ao botão `btn-executar-limpeza` na primeira renderização, evitando duplicação.
- `execute()`: Acionado pelo botão. Mostra modal de confirmação. Se confirmado, aciona bridge e aguarda job, mostrando progresso no overlay global de feedback.
- `renderizarLimpeza()`: Trata o retorno (tanto erro como sucesso) e renderiza no container `conteudo-limpeza`.
- `formatarBytes()`: Função utilitária para converter os bytes liberados (uso exclusivo desta página por enquanto).

### Contratos e Dependências
- **Endpoint Utilizado:** `executar_limpeza`
- **Job ID recebido:** `Phoenix.bridge.call("executar_limpeza")`
- **Espera:** `Phoenix.jobs.awaitJob(job_id)`
- **Payload Esperado Final:** `{ok: true, espaco_liberado_mb: 123.45}` ou `{ok: false, erro: "..."}`
- **Categorias no backend:** Temp do Windows, Temp do usuário, Cache de prefetch, Logs do Windows Update, Relatórios de erro do Windows, Cache de miniaturas, Cache do Chrome, Cache do Edge, Lixo de instaladores, Cache de fontes do Windows, Dumps de memória, Cache do Firefox, Lixeira, Cache de DNS. (São exclusivas do backend, a GUI exibe apenas o total liberado).
- **Proteção contra concorrência:** Implementada flag `executando` interna no escopo da IIFE.
- **Overlays e Feedbacks:** A limpeza inicia diretamente ao clicar sem confirmação prévia, exibindo o overlay global com `Phoenix.ui.feedback`. (Caso haja desejo de confirmação futura, deverá ser implementada como feature separada).
- **Comportamento em Falha de Bridge ou Timeout de Job:** Erros desarmam o overlay, liberam a flag e expõem a mensagem ao usuário.
- **Tamanho atual app.js**: Aproximadamente 974 linhas.

## Otimização (`gui/js/pages/otimizacao.js`)

**Rota:** `otimizacao`
**Namespace:** `Phoenix.pages.otimizacao`

### Funções
- `load()`: Associa os event listeners aos botões da página de otimização (Geral, Gaming, Disco, Liberar RAM, Analisar Startup) caso ainda não estejam associados.
- `executeGeneral()`: Aciona a otimização geral, executando de forma protegida via `Phoenix.operations.restorePoint.runProtected`.
- `executeGaming()`: Aciona a otimização para jogos (também protegida).
- `optimizeDisk()`: Executa a otimização de disco (não usa ponto de restauração, direto pela bridge).
- `releaseStandbyMemory()`: Limpa a RAM Standby (não usa ponto de restauração).
- `analyzeStartup()`: Analisa entradas de inicialização do sistema (não usa ponto de restauração, renderiza lista de programas).
- `exibirResultadoOtimizacao()`: Utilitário para renderização de conclusão das otimizações.

### Contratos e Dependências
- **Endpoints:** 
  - `executar_otimizacao_geral` (job)
  - `executar_otimizacao_gaming` (job, pass `false`)
  - `otimizar_disco` (job)
  - `liberar_memoria_standby` (job)
  - `analisar_startup` (job)
- **Operações que exigem Ponto de Restauração:** Otimização Geral e Otimização Gaming. Ambas delegam o wrapper para `Phoenix.operations.restorePoint.runProtected(fn)`.
- **Proteção Concorrente:** Possui flags locais (`executandoGeral`, `executandoGaming`, `executandoDisco`, `executandoRam`, `executandoStartup`) para prevenir duplicação de solicitações na mesma sub-rotina.
- **Overlays e Modais:** Utiliza `Phoenix.ui.feedback`.
- **Estado:** Ponto de restauração utiliza indiretamente o `Phoenix.state.restorePointCreatedThisSession`.
- **Resultado:** Renderizados dentro do DOM no container de `resultado-otimizacao` ou `resultado-startup`.
- **Política de Falha:** Erros cancelam a operação específica, fecham overlay e loggam no console, não travando a página.


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
