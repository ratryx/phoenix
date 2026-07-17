# Manual Smoke Checklist

Esta lista deve ser executada no Windows (em ambiente de teste ou máquina virtual) após cada fase da refatoração para garantir que o comportamento funcional não foi quebrado.

**Itens marcados com "[Admin]" requerem execução do programa como Administrador.**

## Inicialização e Interface
- [ ] Aplicação abre em modo GUI.
- [ ] Aplicação abre em modo CLI.
- [ ] Janela frameless (GUI) pode ser arrastada clicando na barra superior.
- [ ] Minimizar janela funciona.
- [ ] Fechar janela funciona.
- [ ] Hardware inicial carrega e é exibido na página inicial e rodapé.
- [ ] Métricas rápidas da página inicial atualizam de forma síncrona/contínua.
- [ ] Erros são apresentados na interface de forma amigável sem causar travamento (crash) da aplicação principal.

## Modo Portable
- [ ] Modo portable permite selecionar cliente ativo (apenas visível se o arquivo PORTABLE existir na raiz).
- [ ] Novo cliente pode ser criado no modo Portable.

## Sensores e Monitoramento
- [ ] Página de sensores (HWMonitor) inicia o polling de atualizações em tempo real ao ser aberta.
- [ ] O polling para imediatamente ao sair da página de sensores para não consumir CPU em excesso.

## Funcionalidades Core
- [ ] Diagnóstico completo conclui e renderiza o relatório final na interface.
- [x] Extração de Limpeza com suíte e cobertura estrutural (commit `c175479`)
- [x] Restore Point (Ponto de Restauração) em módulo de operação (compartilhado por Otimização e Rotina Completa)
- [x] Extração de Otimização (Geral, Gaming, Disco, RAM, Startup)
- [Admin] [ ] Limpeza completa conclui com sucesso, exibindo o espaço liberado em MB/GB.
- [Admin] [ ] Ponto de restauração do sistema pode ser criado com sucesso.
- [Admin] [ ] Otimização geral conclui.
- [Admin] [ ] Otimização gaming conclui.
- [ ] Serviços Windows são listados na aba de Serviços.
- [ ] O histórico de execuções anteriores (Atendimentos) é carregado corretamente.

## Rotina Completa
- [Admin] [ ] Execução da "Rotina completa" funciona de ponta a ponta, processando diagnóstico, limpeza, otimização e diagnóstico final.
- [Admin] [ ] O relatório final da rotina completa é gerado corretamente na pasta de logs.
