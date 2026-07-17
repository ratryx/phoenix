# GUI API (PhoenixAPI)

## Responsabilidade
A classe `PhoenixAPI` (localizada em `modules/gui/api.py`) atua puramente como a camada de "Bridge" (ponte) entre o front-end JavaScript (rodando via pywebview) e os serviços backend em Python. Sua função é receber as chamadas via `pywebview.api`, processar os argumentos e delegar a execução para as camadas subjacentes do sistema, retornando um payload serializável (dicionários, listas, primitivos).

## Localização e Separação
Anteriormente integrada no arquivo aglutinador `gui_app.py`, a classe agora está restrita ao arquivo `modules/gui/api.py`.
O arquivo `gui_app.py` tornou-se um mero script de "Bootstrap", contendo somente a lógica de inicialização de interface gráfica, construção das injeções de dependência, instanciação do `pywebview` e o início do _event loop_. A separação garante ausência de _imports circulares_ e coesão estrutural (Clean Architecture).

Para fins de retrocompatibilidade temporária, a `PhoenixAPI` está sendo re-exportada no topo de `gui_app.py`. Novos consumos e testes devem utilizar importação direta:
```python
from modules.gui.api import PhoenixAPI
```

## Dependências Injetadas
A classe depende estruturalmente da injeção explícita de serviços de domínio para funcionar, não gerenciando essas responsabilidades sozinha:
* **JobManager (`self._job_manager`)**: Gerencia o despacho, _threading_ seguro e TTL de chamadas assíncronas (Jobs). A API não constrói mais threads nativas `threading.Thread` manualmente.
* **HardwareService (`self._hardware_service`)**: Prove a leitura limpa e persistência no cache de hardwares, isolando o framework de coletores complexos como `psutil` ou `GPUtil`.
* **WindowController (`self._window_controller`)**: Gerencia as operações matemáticas de drag, redimensionamento, offset de cliques, minimização e fechamento da janela nativa.

## Responsabilidades que permanecem na API
A API ainda guarda alguns atributos residuais que aguardam serviços dedicados:
* `_hw_info`: Payload nativo original recebido no boot (embora as consultas deleguem ao HardwareService).
* `_id_atendimento` e `_nome_cliente`: Estados temporários simulando uma "sessão" ativa para gravação de logs e relatórios finais (candidatos à extração posterior num SessionManager).

## Operações Síncronas x Assíncronas
Métodos síncronos da `PhoenixAPI` geralmente delegam em chamadas O(1) diretas (ex: `obter_hardware`, `iniciar_drag`).
Métodos assíncronos que correm o risco de bloquear a interface gráfica ou a _bridge COM_ (Windows) são imediatamente encapsulados pelo método utilitário `self._iniciar_job()`.
Esta rotina entrega a carga ao `JobManager`, devolvendo para o front-end um objeto padronizado com o _ID da tarefa_:
```json
{ "job_id": "uuid-da-tarefa" }
```
O front-end consumirá periodicamente `verificar_tarefa(job_id)` até recolher a resolução processada (polling não-bloqueante).

## Limitações / Regras
- **Sem Motor Nativo**: `modules/gui/api.py` **NÃO IMPORTA** o módulo global `webview`. Não constrói janelas nativas nem aciona motores C++. Tudo trafega pelo *WindowController*.
- **Sem Estado Mutável Físico**: Não há _tracking_ de posição X/Y nem objetos nativos do Windows guardados no escopo desta classe. O dict `__dict__` não detém referência `_janela`.
