# Execução de Comandos no Windows

Este documento descreve os padrões estabelecidos para a execução de processos e comandos nativos no Windows dentro do **Phoenix Optimizer**.

## Filosofia e Diretrizes

O sistema Phoenix Optimizer interage diretamente com o sistema operacional Windows para modificar configurações de registro, serviços, plano de energia e executar utilitários do sistema (`sc`, `defrag`, `powercfg`, `Get-CimInstance`). 

Para garantir a estabilidade e a responsividade da interface gráfica, toda execução de processos segue as seguintes diretrizes:

1. **Centralização (`run_windows_command`)**: Toda a execução em tempo de execução ("runtime") de subprocessos que manipulam ou consultam o sistema operacional **deve** usar a função `run_windows_command` definida no módulo `modules.core.windows_command`.
2. **Abstenção do módulo `subprocess` no fluxo de domínio**: É proibido importar e utilizar o módulo `subprocess` do Python em arquivos das pastas `modules/` ou `gui/` para executar processos operacionais. As exceções ficam restritas unicamente aos testes ou quando absolutamente necessário fora do escopo principal (ex. atualizações de auto-restart que exigem desconexão).
3. **Gerenciamento Unificado de Falhas**: Exceções geradas pelos processos nativos devem ser capturadas e convertidas num payload de falha padronizado (`CommandResult.ok == False`), evitando que stacktraces quebrem o frontend (`pywebview`).
4. **Tratamento de Timeouts e Cancelamentos**: Todos os comandos têm suporte a timeout (`timeout_seconds`) e podem ser cancelados cooperativamente a pedido do usuário (passando a propriedade `cancel_event` proveniente do `JobManager`).

## Estrutura do Runner

O runner `run_windows_command` fornece as seguintes garantias técnicas:
- **Ausência de Janelas Pretas**: Uso automático da flag `CREATE_NO_WINDOW` no Windows para evitar flashes incômodos no terminal.
- **Process Group Isolation**: Os processos são criados em seus próprios process groups (`CREATE_NEW_PROCESS_GROUP`), garantindo que possam ser finalizados sem abater a aplicação pai (a própria GUI do Phoenix Optimizer).
- **Encerramento Profundo (`taskkill /T /F`)**: Diante de timeout ou cancelamento, a função utiliza `taskkill` na árvore de processos para mitigar instâncias zumbis de processos "teimosos" comuns em comandos Powershell.
- **Leitura Segura e Assíncrona de Outputs (Pipes)**: Os fluxos `stdout` e `stderr` são lidos utilizando threads dedicadas e decodificados usando múltiplas codificações heurísticas (`utf-8`, `utf-16`, e `cp1252`), lidando com as restrições variadas do ambiente Windows.
- **Prevenção de Estouro de Memória**: O runner impõe um limite máximo (`MAX_OUTPUT_BYTES`) para truncar saídas gigantes que de outra forma esgotariam a RAM ou sobrecarregariam a interface web.

## Retorno Seguro e Interface com a Web

O objeto `CommandResult` retornado por `run_windows_command` é restrito ao contexto do servidor local em Python.

Para enviar resultados e metadados com segurança para o frontend (Javascript através de `pywebview`), utiliza-se a função auxiliar `to_public_result`. Ela converte a resposta num dicionário padronizado:

```json
{
    "ok": false,
    "codigo": "COMMAND_FAILED",
    "erro": "Falha ao desativar serviço."
}
```

Essa estrutura previne a exposição indesejada e perigosa de informações, garantindo:
- Omissão da linha de comando executada e do respectivo nome do processo.
- Omissão da saída padrão (`stdout`) (a menos que seja uma execução limpa e validada).
- Omissão completa da saída de erros padrão (`stderr`) na Web, protegendo registros de caminhos de arquivos e contas locais de acesso indesejado.
- Ocultamento dos tracebacks técnicos do Python.

## Cancelamento Cooperativo (Jobs)

A arquitetura de *Jobs* (tarefas em background na camada `gui`) interage ativamente com o núcleo através do objeto `cancel_event` (`threading.Event`). 

Funções demoradas como `executar_otimizacao_geral` e `otimizar_disco_principal` recebem o `cancel_event` através do argumento homônimo e o injetam no comando correspondente:

```python
resultado = run_windows_command(
    ["defrag", "C:", "/O"],
    operation_name="Otimizar Disco",
    timeout_seconds=300.0,
    cancel_event=cancel_event
)
```

Se o frontend requisitar um aborto ou a própria aplicação for fechada, o `JobManager` define o evento `cancel_event.set()`. O runner captará essa mudança durante o processo (ou imediatamente se ele ainda não tiver iniciado) e engatilhará o sistema de *Taskkill*, retornando o código `"COMMAND_CANCELLED"` (`JobCancelledError`).
