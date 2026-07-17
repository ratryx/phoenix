# Sistema de Jobs Atual (Python -> JavaScript)

O sistema de jobs é o coração assíncrono do projeto Phoenix Optimizer, permitindo que a interface web permaneça responsiva enquanto operações lentas ocorrem no backend Python.

## Estrutura Básica e Funcionamento

1. **Estado em Memória (`_tarefas`)**:
   No arquivo `gui_app.py`, existe um dicionário global chamado `_tarefas` que age como um registro em memória.
   Sua estrutura é: `job_id -> {"status": str, "resultado": any, "progresso": int, "mensagem": str}`.

2. **Criação do Job ID e Thread**:
   Quando o frontend (JS) chama um método que requer execução prolongada, o Python aciona o utilitário `_iniciar_job`. 
   Ele cria um UUID4 exclusivo para identificar a operação e o adiciona ao dicionário `_tarefas` com status `"running"`. Em seguida, inicia uma thread (`threading.Thread(target=worker, daemon=True).start()`) que executará a função alvo. A função principal da API então retorna imediatamente `{"job_id": "..."}` para o JS.

3. **Polling no Frontend**:
   A função global JS `awaitJob(jobId)` consulta `verificar_tarefa(job_id)` a cada **500 ms**.
   Ela continua verificando repetidamente até o status da resposta mudar de `"running"` para `"done"` ou `"not_found"`.

## Estados Possíveis

- `"running"`: A tarefa está em andamento.
- `"done"`: A tarefa concluiu, com sucesso ou falha, e contém a propriedade `resultado`.
- `"not_found"`: O Job ID não existe ou o dicionário não o contém. (Retornado preventivamente pela função `verificar_tarefa`).

## Formato dos Resultados (Payload final)

Quando o status é `"done"`, o worker atualiza o job e salva a resposta em `resultado`:
- **Sucesso (Padrão Geral)**: `{"ok": True, ... (demais dados da resposta)}`.
- **Erro**: Se houver exceção na thread, é capturada por um bloco try/except genérico no worker e salva em `resultado` como: `{"ok": False, "erro": str(e), "detalhe": traceback.format_exc()}`. A thread não morre sem avisar.

## Limitações e Riscos na Implementação Atual

* **Expiração e Limpeza (Memory Leak)**: **Inexistente.** Não há expiração ou mecanismo de limpeza no `_tarefas`. Todo job gerado durante uma sessão da aplicação permanecerá carregado na memória do dicionário até que o aplicativo seja fechado.
* **Timeout**: O frontend possui um timeout de 60 segundos (120 consultas de 500ms). Porém, o backend Python **não possui timeout**. A thread continuará rodando indeterminadamente e presa caso a chamada que a originou trave.
* **Cancelamento (Kill / Abort)**: **Inexistente.** Uma vez que o job é iniciado no Python, a thread roda até sua natural conclusão. O frontend não possui mecanismo de aviso para abortar a thread caso o usuário saia da página ou feche a interface de carregamento.
* **Jobs Destrutivos Simultâneos**: **Possível (Risco Alto).** Não há Mutex ou flag global (Lock) no backend que impeça que duas otimizações ou limpezas sejam chamadas sequencialmente ou paralelamente pela interface gráfica, o que poderia corromper o sistema.
* **Abandono do Frontend**: Se o frontend inicia um job, e a página for trocada (cancelando o aguardo via erro de escopo de JS se houvesse, ou se o usuário reiniciar a página caso houvesse F5), o job continuará em processamento silencioso no Python.
