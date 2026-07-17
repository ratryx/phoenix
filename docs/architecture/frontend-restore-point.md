# Frontend Restore Point (Operação Compartilhada)

**Arquivo:** `gui/js/operations/restore-point.js`
**Namespace:** `Phoenix.operations.restorePoint`

Este módulo centraliza e isola o fluxo seguro para criação de ponto de restauração, protegendo operações destrutivas ou críticas.

## Responsabilidade
Concentrar a verificação se o ponto já foi criado na sessão, invocar o endpoint da bridge para criação, tratar o resultado (sucesso, falha ou timeout), abrir o modal interativo em caso de falha permitindo que o usuário decida abortar ou prosseguir, e ao fim (caso permitido) invocar a rotina protegida originalmente fornecida. Garante proteção para que requisições simultâneas não quebrem o fluxo (proteção de concorrência).

## Estado da Sessão
O módulo compartilha o estado definido em `Phoenix.state`:
- `restorePointCreatedThisSession`: Flag booleana persistida em memória durante o runtime do frontend que garante que o ponto seja criado apenas uma vez por sessão.

## Endpoints e Jobs
- **Endpoint:** `criar_ponto_restauracao` (assíncrono, retorna `job_id`)
- **Espera:** Usa `Phoenix.jobs.awaitJob`

## Comportamento
- **Sucesso:** Marca `STATE.restorePointCreatedThisSession = true` e prossegue automaticamente chamando a função da ação (action callback).
- **Falha/Erro:** Usa `Phoenix.ui.feedback.confirmarModal` (através do wrapper preservado `exibirModalRestauracao` renomeado/encapsulado, ou usando a lógica nativa legada) permitindo ao usuário "Continuar mesmo assim" ou "Cancelar". 
- **Continuar:** Se o usuário escolher prosseguir após falha, também marca a flag da sessão como `true` (para não repetir a mensagem de falha em outras otimizações) e chama a ação.
- **Abortar:** Cancela o fluxo, e a função da ação não é executada.

## Proteção e Concorrência
Possui flag interna (`criandoPonto`) que impede múltiplas chamadas simultâneas de atropelarem o fluxo. Assim que a operação completa (com erro, sucesso ou cancelamento), a flag é liberada.

## Consumidores
- `Phoenix.pages.otimizacao`
- `executarRotinaCompleta` (em `app.js`)

## Limitações
A lógica de Ponto de Restauração é altamente acoplada ao sistema Windows via backend. O frontend foca apenas no controle de sessão e feedbacks visuais, não fazendo validações de disco ou permissões diretamente.
