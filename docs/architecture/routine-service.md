# RoutineService

O `RoutineService` (`modules/core/routine_service.py`) é o responsável por centralizar a lógica de negócio do fluxo principal (rotina completa) do Phoenix Optimizer, orquestrando sequencialmente diversas camadas de negócio da aplicação.

## Responsabilidades
- Coordenar a execução ordenada das etapas primárias: diagnóstico inicial, limpeza, otimização, diagnóstico final e geração de relatórios.
- Encapsular os chamados diretos aos módulos globais de lógica de negócios (como `diagnostico`, `limpeza`, `otimizacao`, `logs`, `relatorio`).
- Consolidar e retornar um payload determinístico padronizado, testável sem qualquer _mocking_ visual.

## Dependências Injetadas
O serviço adota Injeção de Dependências em seu construtor, aceitando por padrão os módulos físicos da aplicação. Isso garante isolamento perfeito em testes de unidade:
- `diagnostico_module`
- `limpeza_module`
- `otimizacao_module`
- `logs_module`
- `relatorio_module`

## Sequência Estrita e Estados
A execução da rotina ocorre em uma sequência bloqueante atômica que preserva as medições:
1. Validação de obrigatoriedade do estado interno da API (`id_atendimento`).
2. Diagnóstico Silencioso (pré-teste) -> Registra Log Inicial.
3. Execução de Limpeza Profunda.
4. Otimização Geral de Performance.
5. Diagnóstico Silencioso (pós-teste) -> Registra Log Final.
6. Exportação do Arquivo Relatório e consolidação de Payload de saída.

*A responsabilidade de estabelecer a "Sessão" de ID Atendimento ainda recai sobre o front-end via `PhoenixAPI`, e o RoutineService requer esses identificadores injetados por parâmetro.*

## Integração com a PhoenixAPI
- A `PhoenixAPI` possui uma instância imutável do `RoutineService` (assim como o `HardwareService`).
- O endpoint `executar_rotina_completa()` em `api.py` **NÃO** importa os módulos lógicos nativos. Ele delega a instrução `self._routine_service.executar()` e a embute em um processo gerenciado pelo `JobManager`.
- O `JobManager` despacha essa instrução numa thread dedicada com trava protetora `system_mutation`.

## Relação com Relatórios e Rollback
O fluxo do `RoutineService` engatilha os _snapshots_ salvando o histórico da evolução do sistema (via `logs.salvar_snapshot`).
Entretanto, o **Ponto de Restauração (Rollback)** é invocado e aguardado logicamente na sub-camada visual Javascript (`app.js` -> `comPontoRestauracao()`) antes mesmo do Job da rotina ser submetido à Python. Isso previne que um erro no WMI (rollback) polua a atomicidade da rotina principal da aplicação.

## Política de Falhas e Concorrência
- **Erros Fatais**: Erros nativos como permissão negada abortam imediatamente a thread do `JobManager` antes da geração de logs e relatório. O front-end absorve a falha fatal.
- **Falhas Recuperáveis**: Os submódulos de otimização/limpeza já silenciam falhas de subsistemas opcionais, devolvendo apenas os dados parciais.
- **Concorrência**: É resguardado de conflitos de estado através do grupo mutante `system_mutation` no `JobManager`, rejeitando _overlappings_.
