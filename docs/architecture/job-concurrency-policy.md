# Política de Concorrência de Jobs (JobManager)

Esta política define como os diferentes métodos assíncronos da `PhoenixAPI` interagem com o `JobManager` para prevenir conflitos e corrupções de estado do sistema, além de proteger a integridade dos dados durante execução de tarefas demoradas.

## Grupos Exclusivos

Operações que realizam alterações no sistema do usuário (mutações) compartilham o grupo exclusivo `system_mutation`. Somente **uma** operação desse grupo pode estar ativa (em status `running`) a qualquer instante.

| Método API | Tipo | Grupo Exclusivo | Pode rodar em paralelo? | Motivo da Decisão |
|------------|------|-----------------|-------------------------|-------------------|
| `executar_limpeza` | Mutação | `system_mutation` | Não | Exclui arquivos reais do disco. Outra limpeza ou otimização rodando junto pode corromper dados. |
| `criar_ponto_restauracao` | Mutação | `system_mutation` | Não | Aciona WMI/PowerShell. Protegido contra gargalos e concorrência nativa do Windows. |
| `executar_otimizacao_geral`| Mutação | `system_mutation` | Não | Altera dezenas de chaves de registro e desativa recursos. |
| `executar_otimizacao_gaming`| Mutação | `system_mutation` | Não | Altera planos de energia e gerencia placa de rede/DNS. |
| `otimizar_disco` | Mutação | `system_mutation` | Não | Dispara o Desfragmentador do Windows. Altamente intensivo em I/O. |
| `desativar_servico` | Mutação | `system_mutation` | Não | Altera o estado e inicialização de um serviço de sistema. |
| `ativar_servico` | Mutação | `system_mutation` | Não | Inicia e altera um serviço do Windows. |
| `liberar_memoria_standby` | Mutação | `system_mutation` | Não | Chama API nativa profunda do Windows, esvaziando cache em RAM. |
| `executar_rotina_completa` | Mutação | `system_mutation` | Não | Encapsula Limpeza, Otimização e Logs, delegando a execução orquestrada ao `RoutineService`. |

## Operações Somente Leitura (Sem Grupo Exclusivo)

Operações focadas em consultar, ler e reportar informações podem executar livremente e paralelamente umas às outras, assim como paralelamente a operações de mutação (embora a mutação pesada possa impactar o desempenho da leitura temporariamente).

| Método API | Tipo | Grupo Exclusivo | Pode rodar em paralelo? | Motivo da Decisão |
|------------|------|-----------------|-------------------------|-------------------|
| `obter_diagnostico` | Leitura | Nenhum | Sim | Apenas processa arquivos e consultas WMI de forma passiva. |
| `carregar_hardware_cache` | Leitura | Nenhum | Sim | Consulta hardware. Possui callbacks de progresso na GUI. |
| `forcar_rescan_hardware` | Leitura | Nenhum | Sim | Recoleta detalhes totais do sistema. |
| `listar_servicos` | Leitura | Nenhum | Sim | Coleta status dos serviços. |
| `analisar_startup` | Leitura | Nenhum | Sim | Apenas verifica registro e pastas de inicialização. |

## Comportamento em Conflito

Quando uma operação de mutação tenta ser lançada pelo frontend e outra já está no status `running`:
1. O JobManager **cria o job** com um novo ID (para satisfazer o retorno síncrono esperado pela ponte `_iniciar_job`).
2. O job é finalizado *imediatamente* na própria thread principal.
3. O frontend receberá, ao consultar a tarefa:
   ```json
   {
       "status": "done",
       "resultado": {
           "ok": false,
           "erro": "Outra operação do sistema já está em execução.",
           "detalhe": "Conflito no grupo exclusivo: system_mutation"
       }
   }
   ```
Isso garante estabilidade, não corrompe a UI do JS, e notifica o usuário gentilmente que ele deve aguardar.
