# Quickstart: Validação da GUI e Spinner

Este documento serve para testar e validar o comportamento visual do Spinner e a transição entre abas (features da US 012).

## Pré-requisitos
1. Ter as dependências Python instaladas (`pip install -r requirements.txt`).
2. Executar a aplicação GUI no Windows: `python launcher.py`

## Cenário 1: Fluidez do Spinner e Non-blocking Thread

1. Acesse a aba **Logs/Histórico** ou clique em **Rotina Completa** no Dashboard principal.
2. Imediatamente após clicar, clique e segure a barra de título da janela e mova-a vigorosamente pela tela.
3. Observe o centro da janela:
   - **Resultado Esperado**: O ícone de *loading/spinner* animado por CSS não congela em nenhum momento (gira suavemente em 60fps), e a janela responde perfeitamente ao mouse durante toda a duração do processo pesado que ocorre no backend.

## Cenário 2: Transição Instantânea de Abas

1. Olhe para a Sidebar (barra lateral ou no topo) contendo os botões de navegação.
2. Clique alternadamente em `Dashboard`, `Otimizações` e `Logs`.
3. **Resultado Esperado**: A transição das áreas visuais ocorre quase que instantaneamente (< 100ms) sem necessidade de re-renderizar a janela inteira. O estado da aba ativa fica realçado na Sidebar.

## Cenário 3: Validação Sem Erros Python/JS

1. Abra o Console de Desenvolvedor (DevTools do Edge WebView2) clicando com botão direito na UI -> "Inspecionar", ou lendo o console via terminal nativo no `python launcher.py`.
2. Realize todas as chamadas de listar serviços e inicialização na interface.
3. **Resultado Esperado**: Nenhum erro de exceção é emitido no terminal. O front-end captura e resolve o `job_id` retornando sucesso via polling, indicando que os 4 métodos refatorados (Listar Serviços, Listar Inicialização, Obter Histórico, Listar Backups) funcionaram perfeitamente no novo modelo assíncrono.
