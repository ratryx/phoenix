# Phase 1: Quickstart Validation Guide

## Validação da Verificação de Otimização (010)

**Pré-requisitos**: Rodar o Phoenix Optimizer como administrador em uma máquina Windows.

1. **Alterar manualmente o Registro/Configuração**
   - Mude o plano de energia para "Economia de Energia".
   - Desative o Modo de Jogo nas Configurações do Windows.
2. **Executar Verificação**
   - Na CLI, selecione a nova opção "Verificar Status das Otimizações".
   - **Resultado Esperado**: O console lista os itens, e aponta o Plano de Energia e Modo de Jogo como inativos ([ERRO] vermelho).
3. **Reaplicar**
   - Na GUI ou CLI, execute o comando de "Reaplicar Todos" ou escolha individualmente a reaplicação.
   - **Resultado Esperado**: O sistema emite log de que as configurações foram ajustadas. Uma nova verificação mostra os itens como ativos ([OK] verde).

## Validação do Cache de Hardware (011)

1. **Geração do Primeiro Cache**
   - Execute o app pela primeira vez e solicite ver o Hardware.
   - **Resultado Esperado**: Um arquivo json é gerado em `%PROGRAMDATA%\PhoenixOptimizer\cache\hardware.json`.
2. **Abertura Rápida**
   - Feche o app e abra-o novamente, solicitando o Hardware.
   - **Resultado Esperado**: O tempo de resposta para ver os dados do hardware é virtualmente instantâneo (dados vêm do cache).
3. **Invalidação (Simulada)**
   - Edite o `%PROGRAMDATA%\PhoenixOptimizer\cache\hardware.json` e altere o `cpu_modelo` para "Test CPU".
   - Abra o app novamente.
   - **Resultado Esperado**: O app detecta divergência (Test CPU != Processador Real), realiza novo scan e regrava o arquivo JSON com o modelo correto.
