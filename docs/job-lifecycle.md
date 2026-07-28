# Ciclo de Vida e Gerenciamento de Tarefas (Job Lifecycle)

O **Phoenix Optimizer** utiliza um gerenciador de tarefas em segundo plano baseado em threads (`JobManager`) para executar operações pesadas, isolando-as do loop principal da Interface de Usuário (UI). Este documento descreve o fluxo, os estados, e as políticas de timeout da arquitetura.

## 1. Visão Geral

O gerenciamento de jobs resolve três problemas críticos:
1. Impede travamentos da UI (o pywebview processa RPCs de forma síncrona).
2. Fornece cancelamento cooperativo seguro.
3. Garante exclusividade de operações destrutivas ou conflitantes (como limpezas concorrentes).

O front-end (`app.js`) realiza chamadas ao método assíncrono exposto `awaitJob`, que periodicamente faz polling (verificação) usando a função `verificar_tarefa` fornecida pela `PhoenixAPI`.

## 2. Estados da Tarefa (Job Status)

Cada tarefa trafega por um ciclo de vida restrito aos seguintes estados:

* `running`: A tarefa está sendo ativamente processada na thread do worker.
* `cancel_requested`: O cancelamento foi solicitado, mas o worker ainda não fez a verificação do checkpoint. O status ainda é tratado essencialmente como "ativo".
* `done`: A tarefa foi concluída com sucesso.
* `failed`: A tarefa encerrou devido a uma exceção não-tratada, ou falha de serialização JSON.
* `cancelled`: O worker aceitou cooperativamente o cancelamento (via `is_cancel_requested()`), e abortou com sucesso a operação pendente.
* `timed_out`: O watchdog do JobManager detectou que a tarefa excedeu o `deadline` permitido e forçou um encerramento (o worker será marcado para abortar no próximo checkpoint de cancelamento).
* `not_found`: O ID do job requisitado não existe ou já foi limpo (TTL expirou).

## 3. Políticas de Timeout e Watchdog

Para evitar que threads fiquem penduradas infinitamente, o `JobManager` embute um watchdog. Ele verifica se as operações ativas excederam o seu respectivo `timeout` estipulado no momento da submissão. 
Essa checagem utiliza `time.monotonic()` e ignora oscilações do relógio do sistema.

A `PhoenixAPI` predefine as seguintes políticas de timeout para suas operações padrão:

* **15 Segundos**: Leitura padrão (diagnóstico de software).
* **30 Segundos**: Leitura demorada (forçar detecção de hardware do zero).
* **180 Segundos**: Mutações do sistema localizadas (Otimizações específicas, Limpeza).
* **600 Segundos (10 min)**: Rotina completa do Phoenix (pode encadear limpezas pesadas, criação de restore points, e mutações de hardware/registro).

Se o tempo esgotar, o `JobManager` define o status como `timed_out` para o front-end liberar a UI (escondendo os overlays de loading) e sinaliza internamente o `cancel_event` para a thread abortar em seu próximo checkpoint de forma segura.

## 4. Cancelamento Cooperativo (Cooperative Cancellation)

O Phoenix Optimizer evita explicitamente "matar" as threads à força para impedir:
* Vazamento de descritores de arquivo ou ponteiros de memória COM.
* Corrupção de Registro do Windows ou Estado Inconsistente.

Tarefas que suportam cancelamento injetam um objeto `JobContext` através do argumento `job_context`. A rotina longa deve espalhar checkpoints:

```python
def rotina(job_context=None):
    if job_context:
        job_context.raise_if_cancelled()
        
    passo_1()
    
    if job_context:
        job_context.raise_if_cancelled()
        
    passo_2()
```

## 5. Exclusividade e Concorrência

Para operações destrutivas, como Limpeza (`executar_limpeza`), utiliza-se o agrupamento exclusivo (`exclusive_group="system_mutation"`).

O JobManager rejeita *imediatamente* (lançando `JOB_CONFLICT`) novas submissões de tarefas desse mesmo grupo se:
1. Houver uma tarefa ativa na fila daquele grupo.
2. A thread do worker atual (mesmo em status cancelado ou com erro lógico reportado) ainda não tiver reportado encerramento limpo (`worker_alive == True`).

Essa garantia baseada em **worker_alive** impede que um segundo job de limpeza inicie enquanto o primeiro, mesmo que cancelado, ainda estende uma deleção crítica no backend.

## 6. Fluxo de Limpeza e Persistência (TTL)

* O `JobManager` não purga imediatamente jobs finalizados. Ele os mantém em memória pelo tempo estipulado em `ttl_seconds` (padrão 15 minutos).
* Isso permite que o frontend faça polling com atraso devido ao frame de animação ou latência de eventos e ainda encontre a resposta.
* A purga final `_cleanup_expired` somente remove da memória as tarefas que não possuem thread viva (garantia contra threads órfãs poluindo estado de concorrência) e estouraram seu limite de tempo.
