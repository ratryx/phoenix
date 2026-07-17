# Sistema Atual de Jobs Assíncronos (Refatorado - v2)

Este documento descreve como a comunicação assíncrona entre o front-end (HTML/JS via `pywebview`) e o back-end (Python) acontece, utilizando o novo componente `JobManager` (`modules/gui/jobs.py`).

## 1. O Problema Original
O `pywebview` não permite facilmente que a renderização da interface continue enquanto o Python executa uma tarefa pesada (como varrer o disco) caso a chamada ocorra na thread principal, congelando o aplicativo.

## 2. A Solução: `JobManager`
Ao invés de processar o comando no ato e travar a GUI, o backend (através de `PhoenixAPI._iniciar_job`) submete a tarefa ao `JobManager`.

A classe gerencia as execuções de forma thread-safe usando `threading.RLock`, aloca um UUID único (o `job_id`), e inicia uma daemon-thread.

1. **JS chama:** `pywebview.api.executar_limpeza()`
2. **Python:** Submete a operação ao `JobManager`, recebe `job_id` e retorna imediatamente `{"job_id": "123"}`.
3. **JS recebe:** O `job_id`. Inicia um *polling* `setInterval`.
4. **JS faz Polling:** Chama `pywebview.api.verificar_tarefa("123")` a cada ~500ms.
5. **Python (`JobManager.consultar`):** Retorna o dicionário interno do job protegido por lock.
6. **Fim do processo:** Quando o status muda de `"running"` para `"done"`, o frontend recebe o resultado final, interrompe o polling e avisa o usuário.

## 3. Estrutura do Dicionário de Job

Internamente, o `JobManager` armazena e consulta cada job sob o formato:
```python
{
    "status": "running" | "done",
    "resultado": None | { ... JSON serializável ... },
    "progresso": 50,              # Opcional
    "mensagem": "Verificando...", # Opcional
    "created_at": 169000000.0,
    "started_at": 169000000.1,
    "completed_at": 169000010.5,
    "operation_name": "executar_limpeza",
    "exclusive_group": "system_mutation"
}
```

O payload devolvido pela função `consultar(job_id)` mascara chaves internas, devolvendo apenas as chaves originais que o front-end espera:
`status`, `resultado`, `progresso`, `mensagem`.

## 4. Política de TTL (Time To Live) e Memory Leak
Anteriormente os jobs rodavam eternamente e acumulavam no dicionário `_tarefas` gerando vazamento de memória.
Agora o `JobManager` implementa **Expiração (TTL)**:
- Jobs concluídos (`"status": "done"`) ficam visíveis no estado do dicionário por, no padrão, 900 segundos (15 minutos).
- Ao realizar nova leitura ou criar novos jobs (`submit` ou `consultar`), o método oportunístico `_cleanup_expired()` remove jobs velhos para limpar memória.
- Jobs em `"running"` nunca expiram, protegendo tarefas legítimas e demoradas.

## 5. Proteção de Concorrência e Race Conditions
Para impedir que dois jobs destrutivos executem ao mesmo tempo (como duas Limpezas simultâneas ou Limpeza e Otimização juntas), há o controle de **Grupos Exclusivos**:
1. Se uma função destrutiva é chamada, ela entra no `exclusive_group="system_mutation"`.
2. O lock salva quem detém o grupo.
3. Se um novo job do mesmo grupo for disparado e o detentor ainda estiver `"running"`, o job secundário é criado, mas terminado *imediatamente* com status `"done"` e `resultado.ok = False`, contendo a mensagem de erro controlada para o frontend.
4. Jobs de "somente leitura" (diagnóstico, hardware) não entram neste grupo, podendo rodar normalmente em paralelo (vide `job-concurrency-policy.md`).

## 6. Tratamento de Exceções
- Exceções ocorridas dentro da `daemon-thread` Python são capturadas (`try...except`) e impedidas de quebrar toda a base.
- O traceback é registrado no arquivo de logs local do usuário (`logger.exception()`).
- O erro é encapsulado no contrato limpo e serializável `{ "ok": False, "erro": str(e), "detalhe": ... }` que o JavaScript lida desenhando um overlay na tela e não matando o fluxo.
- Há validação estrita embutida no worker que tenta aplicar `json.dumps()` para testar se o resultado pode ser convertido no `pywebview`. Caso falhe, retorna falha de serialização antes que trave a bridge nativa C/C++ do Windows.

## 7. Limitações (Ausência de Cancelamento Forçado)
Em Python padrão, não é recomendável ou trivial interromper uma thread de sistema rodando de maneira arbitrária por fora, especialmente se estiver engatada numa API externa pesada como WMI/PowerShell. Sendo assim:
- **Não há aborto forçado:** O Cancelamento pela interface do Phoenix atualmente desiste do polling, fechando o modal para o usuário, mas o backend concluirá a rotina até o fim (ela é "fire-and-forget"). O front-end simplesmente para de perguntar. 
