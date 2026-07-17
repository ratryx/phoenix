# Window Controller

## Responsabilidade
O `WindowController` (localizado em `modules/gui/window_controller.py`) é o componente dedicado e isolado responsável por gerenciar as interações físicas e de estado com a janela frameless (sem bordas nativas) gerada pelo `pywebview`. 
Ele absorve totalmente a responsabilidade de movimentação por drag, armazenamento do objeto visual, minimizar e destruir a janela.

## Estado Privado
O controlador armazena internamente:
- `_window`: Referência para a janela nativa do pywebview. Pode ser None em ambientes de teste.
- `_is_dragging` (bool): Flag indicando se a janela está atualmente sendo arrastada.
- `_drag_start_mouse_x` / `_y`: Ponto inicial de clique do mouse (em tela).
- `_drag_start_win_x` / `_y`: Ponto inicial top-left da janela no momento do clique.

## Ciclo do Drag
1. **iniciar_drag(x, y, win_x, win_y):** O JavaScript aciona o evento `mousedown` na top-bar e repassa as coordenadas atuais do mouse e janela para a bridge. O controlador salva esses dados e ativa a flag de drag.
2. **mover_janela(x, y):** Ocorre ininterruptamente via `mousemove` no frontend. O controlador calcula o delta entre o clique inicial e o atual, soma à posição inicial da janela e utiliza `window.move(new_x, new_y)` para refletir o deslocamento.
3. **parar_drag():** Ocorre no `mouseup`. A flag de drag é redefinida para False, parando a resposta aos eventos de movimento pendentes.

## Integração com a API
A classe `PhoenixAPI` foi purificada para atuar apenas como roteador (bridge). Ela não possui mais atributos de posição ou de janela nativa. Seus métodos expostos publicamente (como `mover_janela`) apenas redirecionam os parâmetros e executam o equivalente no `_window_controller` instanciado durante o boot. O payload de retornos e assinaturas permaneceu exatamente igual, sem impacto para `app.js`.

## Integração com o Bootstrap
No arquivo de entrada (`modules/gui_app.py` -> `iniciar()`), a inicialização segue um ciclo rigoroso de injeção de dependência:
1. Constrói-se os serviços (`HardwareService`, `WindowController`).
2. Constrói-se a bridge (`PhoenixAPI`), injetando os serviços no construtor.
3. O `webview.create_window` é executado, absorvendo a `PhoenixAPI` já engatilhada.
4. Após o retorno do objeto da janela criada (e imediatamente antes do `webview.start()`), executa-se o método explícito `window_controller.set_window(janela)`.

## Comportamento Sem Janela
Testes unitários e instâncias headless evitam erros operacionais. Se `_window` for None, os comandos de `minimizar`, `fechar` e `mover_janela` atuam como no-ops, evitando acidentes de ponteiro nulo (NullPointer). Isso viabilizou testes com injeção de dependência via FakeWindow.

## Tratamento de Erros
Todas as chamadas recebidas do JS são embaladas por diretivas seguras (`try... except Exception:`) acionando internamente o `logger.exception`. Desta forma:
- Falhas de sistema na comunicação COM/nativa do pywebview não invadem o Javascript (protegendo a serialização).
- Coordenadas defeituosas que quebram o parsing numérico apenas invalidam o arraste local, mas não derrubam o serviço contínuo de diagnósticos de base.

## Thread Safety
Embora eventos da interface do `pywebview` costumem ser encadeados, a bridge pode rodar num pool concorrente. Por precaução para não corromper o cálculo de offsets (drag offset overlap) sob rápida sucessão de eventos, o controlador aplica um `threading.RLock()` simples ao redor do bloco de leitura e escrita das variáveis e chamadas de movimento.
O bloqueio (lock) é fino e restrito apenas ao acesso das variáveis, liberando o processo rapidamente.

## Limitações Atuais
- Não há suporte oficial a múltiplas janelas (múltiplas referências nativas) de forma concorrente nesta etapa, visto que não é o requisito do Phoenix (Single Page/Single Window App).
- Apenas movimento é mapeado. Eventos complexos como snap nativo do Windows e redimensionamento não estão integrados ainda.
