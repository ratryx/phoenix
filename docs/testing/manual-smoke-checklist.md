# Manual Smoke Test Checklist

Este checklist deve ser executado por um operador real no Windows antes de aprovar o merge da branch refatorada (`refactor/architecture-v2`) para a `main`. A validação ocorrerá preferencialmente em Máquina Virtual descartável devido aos testes destrutivos.

## Inicialização
- [ ] O aplicativo abre normalmente.
- [ ] O bootstrap ocorre apenas uma vez e estabiliza a UI.
- [ ] Cliente portable atual/salvo é carregado corretamente no header e variáveis.
- [ ] A tela de Modo Portable com a lista de clientes aparece se o modo estiver ativo.
- [ ] Sidebar renderiza corretamente e realça a seleção atual.
- [ ] O controle nativo de Drag na Titlebar funciona perfeitamente sem input lag no mouse.
- [ ] A navegação por hash (`#`) funciona (avançar e voltar usando atalhos de mouse se suportado ou observando o ID).
- [ ] Minimizar abaixa a aplicação para a barra de tarefas.
- [ ] Fechar a aplicação a encerra sem travamentos de processo zumbi.

## Somente leitura (Seguro)
- [ ] Início: Cards exibidos, dados macros carregados.
- [ ] Diagnóstico: Varredura de metadados exibe valores corretos.
- [ ] Hardware: Listagem aprofundada do equipamento, expansão/retração de abas de dispositivo.
- [ ] Sensores: O polling em tempo real carrega processamento, memória e temperaturas, alterando a cor percentual dinamicamente.
- [ ] Histórico: Dados de clientes renderizam tabela coerentemente.
- [ ] Relatório: Tentar acessar o relatório isoladamente exibe o fallback limpo de "vazio".

## Operações controladas (Em VM Descartável)
- [ ] Limpeza: Clicar aciona modal de confirmação. Operação exclui temp sem travamentos e barra preenche.
- [ ] Otimização Geral: Conclui com êxito os ajustes de sistema previstos.
- [ ] Otimização Gaming/Disco/RAM Standby/Startup: Teste empírico de um sub-item.
- [ ] Serviços do Windows: Desabilitar um serviço específico funciona de forma modular refletindo o status dinâmico na tela.
- [ ] Ponto de Restauração: Operação paralela de PowerShell funciona e avisa quando finalizada.
- [ ] Rotina Completa: Executa sequência. Mostra overlay. Passa sem erro. 
- [ ] Relatório Final: O Relatório é exibido no final da rotina com todos os deltas detalhados (exibindo badges, cor de sucesso e formatações customizadas).

## Concorrência e falhas
- [ ] Duplo Clique: Clicar desesperadamente várias vezes no botão da Rotina Completa só aciona a rotina uma única vez.
- [ ] Conflito de jobs: Tentar iniciar outra macro enquanto a Limpeza ou Rotina rodam é ignorado ou rejeitado suavemente.
- [ ] Timeout: Bloqueio do Backend por tempo anormal falha com aviso tratável e permite continuação.
- [ ] Falha de Restore Point: Negar o ponto de restauração, mas confirmar que quer prosseguir a otimização com o modal vermelho, roda o comando com sucesso no backend.
- [ ] Abortar Restore Point: Recusar continuar pelo ponto de restauração cancela e não quebra/trava a tela.
- [ ] Falha de Permissão / Suporte de API: Lida bem se falhar para coletar CPU/GPU ou não tiver previlégios.
- [ ] Ausência de Sensores / Ausência de GPU: Renderiza fallback tolerante ou omite o componente na tabela, sem estourar exception não tratada no frontend.
- [ ] Payload vazio no backend de cliente: Não adiciona lixo no display de dados.

| Grupo                    | Resultado Esperado / Status  | Evidência | Observações | Aprovação |
|--------------------------|------------------------------|-----------|-------------|-----------|
| Inicialização            | Passagem Total                |           |             | [ ]       |
| Somente leitura          | Componentes carregam          |           |             | [ ]       |
| Operações controladas    | Efeitos Reais + Overlays      |           |             | [ ]       |
| Concorrência e falhas    | Sobrevivência e Tratamento    |           |             | [ ]       |
