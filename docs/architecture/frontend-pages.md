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

## Serviços (`gui/js/pages/servicos.js`)

**Rota:** `servicos`
**Namespace:** `Phoenix.pages.servicos`

### Funções Atuais (antes da extração)
- `carregarServicos`: Busca a lista e renderiza na tela.
- Ouvintes anônimos dentro de `carregarServicos`: Um listener `click` para cada toggle.

### Contratos e Dependências
- **Endpoints Utilizados:**
  - `listar_servicos` (Síncrono/Assíncrono: Assíncrono com job `awaitJob`). Payload das entradas: `[{nome_servico, nome_amigavel, descricao, status}]`
  - `ativar_servico` (Assíncrono com job). Payload: string `nome_servico`
  - `desativar_servico` (Assíncrono com job). Payload: string `nome_servico`
- **IDs do DOM:** `#conteudo-servicos`
- **Classes/Elementos:** `.toggle`, `.bola`, `.badge`, `.sucesso`, `.neutro`, `.ativo`, `.tabela-dados`, `.card`
- **Listeners:** Click nos botões `.toggle` com data-attributes `data-servico` e `data-ativo`.
- **Estado Local:** O status atual ("Rodando" vs "Parado") é salvo localmente na class `.ativo` e atributo `data-ativo` do botão, atualizando a UI otimisticamente após o job retornar sucesso (`{ok: true}`). A lista inteira não recarrega.
- **Filtros/Busca:** Não existem filtros nem busca nativamente nesta tela.
- **Confirmação/Proteção Existente:** Usa Ponto de Restauração em cada mutação de serviço via `Phoenix.operations.restorePoint.runProtected(async function() {})`. Portanto, qualquer tentativa de ativação ou desativação exigirá ou já usará o ponto de restauração, com todos os seus modais nativos.
- **Serviços Protegidos/Bloqueados:** O Frontend não faz distinção se um serviço é protegido. Ele exibe e atacha eventos para todos que vêm na listagem. O Backend envia unicamente a lista baseada em seu dict interno `SERVICOS_SEGUROS` e descarta implicitamente qualquer serviço crítico.
- **Overlay/Feedback:** Usa `Phoenix.ui.feedback.mostrarOverlay()` indicando a mudança e o encerra no finally.
- **Estados de Serviço:** "Rodando" (sucesso), "Parado" / "Não encontrado" / "Desconhecido" / "Erro ao consultar" (neutro). A renderização checa estritamente `status === "Rodando"` para setar a variável de interface `ativo = true`.
- **Globals/Dependências Restantes:** Nenhuma global específica. Necessita de `Phoenix.bridge`, `Phoenix.jobs`, `Phoenix.operations.restorePoint`, `Phoenix.ui.feedback`.

## Histórico (`gui/js/pages/historico.js`)

**Rota:** `historico`
**Namespace:** `Phoenix.pages.historico`

### Funções Atuais (antes da extração)
- `carregarHistorico`: Busca a lista estática e a renderiza na tela através do overlay.

### Contratos e Dependências
- **Endpoints Utilizados:**
  - `obter_historico` (Assíncrono com job `awaitJob`). Payload das entradas: `{ok: true, atendimentos: [{id_atendimento, cliente, data_hora}]}`
- **IDs do DOM:** `#conteudo-historico`
- **Classes/Elementos:** `.card`, `.tabela-dados`, `.texto-secundario`, `.badge`, `.erro`
- **Listeners:** Nenhum. A tabela de listagem de atendimentos atual é estritamente de exibição em tabela estática (não possui clicks, links, rolagem infinita nem botões expansíveis).
- **Estado Local:** O histórico recarrega inteiramente toda vez que a página é visitada pela rota do aplicativo. Não cacheia client-side e não altera flags isoladas.
- **Filtros/Ordenação:** Não existem implementações de filtros ou buscas.
- **Detalhes / Snapshots:** Funcionalidades de visualização do histórico como comparação Antes/Depois, expansão de detalhes completos com labels não são realizadas ou processadas aqui (são geradas e exibidas no endpoint de "Relatório" da Rotina Completa, ou ausentes no baseline do Histórico puro).
- **Rollback / Limpeza:** Não estão presentes no código original deste commit. Inexistente exclusão ou restauração pontual via histórico do atendimentos.
- **Proteções / Concorrência:** O carregamento da página apenas utiliza o job de feedback assíncrono.
- **Overlay:** Usa o `Phoenix.ui.feedback.mostrarOverlay("Consultando histórico...")` no request.
- **Fronteira com Relatório:** A geração do relatório e sua visualização comparativa estão restritas a `app.js` (`renderizarRelatorio`) através da função de "Rotina Completa". A página do Histórico é um leitor primitivo do log.
- **Globals/Dependências Restantes:** Nenhuma exposta. Necessita das instâncias `Phoenix.bridge`, `Phoenix.jobs` e `Phoenix.ui.feedback`.

## Relatório (`gui/js/pages/relatorio.js`)

**Rota:** `relatorio`
**Namespace:** `Phoenix.pages.relatorio`

### Funções Atuais (antes da extração)
- `renderizarRelatorio(resultado)`: Exclusiva no `app.js`, injeta estaticamente as comparações no DOM.

### Contratos e Dependências
- **Origem dos Dados:** Política C — HTML montado imediatamente. A página não busca seu estado num endpoint nem o armazena em variável. Ela é chamada diretamente pela Rotina Completa no frontend.
- **Payload da Rotina Completa:** 
  ```json
  {
    "ok": true,
    "antes": { "cpu": { "uso_percentual": 0.0 }, "memoria": { "percentual_uso": 0.0, "disponivel_gb": 0.0 } },
    "depois": { "cpu": { "uso_percentual": 0.0 }, "memoria": { "percentual_uso": 0.0, "disponivel_gb": 0.0 } },
    "espaco_liberado_mb": 0.0,
    "relatorio_txt": "C:\\..."
  }
  ```
- **IDs do DOM:** `#conteudo-relatorio`.
- **Cálculos Frontend e Deltas:**
  - `linhaComparativa` processa `depois - antes`.
  - Tolerância de `< 0.01` é classificada como `"neutro"` (sinal `=`).
  - Lógicas booleanas dependentes (`menorEMelhor`): CPU e RAM de uso são invertidas vs RAM disponível.
  - Símbolos: `▼` e `▲`. Arredondamento numérico `Math.abs(diferenca).toFixed(1)`.
- **Modais e Botões:** Inexistentes nesta página. A string bruta de exportação do `.txt` apenas é colocada no footer sem links ou botões de "Abrir Relatório".
- **Estado Vazio e Erros:** Não há tratamento. A ausência do JSON explodiria o DOM, pois o `app.js` verifica o erro em `executarRotinaCompleta` antes de chamar este método.
- **Fronteira:** O Histórico não se comunica com ela. A Rotina Completa gera os dados via Job no backend, faz `navigate("relatorio")` e só então injeta os blocos formatados de variação em tela.
