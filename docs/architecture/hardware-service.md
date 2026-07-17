# HardwareService

O `HardwareService` (`modules/core/hardware_service.py`) é o responsável por isolar a camada de apresentação (`PhoenixAPI` e a interface gráfica) das bibliotecas e mecanismos diretos de coleta de hardware do sistema operacional (como `psutil`, `platform` e `GPUtil`).

## Responsabilidades
- Fornecer métricas rápidas e assíncronas para o frontend de forma centralizada.
- Normalizar dados do sistema, de discos, de GPU e de memória.
- Proteger a API contra falhas de bibliotecas opcionais (ex: `GPUtil` ausente ou drivers de GPU não suportados).
- Servir como adaptador entre as requisições de front-end (bridge) e a coleta profunda legada mantida em `modules/hardware.py`.
- Lidar com operações síncronas de leitura em background sem travar a aplicação, servindo valores default/fallback em caso de exception, e reportando logs puramente no backend.

## Dependências
O serviço foi desenhado para aceitar injeção de dependências. Em tempo de execução real, ele utiliza as seguintes bibliotecas:
- `psutil`: I/O, métricas de memória, uso de processador por núcleo, uptime e boot time.
- `GPUtil`: Uso, memória e temperatura das GPUs detectadas. Se não estiver instalado, a coleta não quebra.
- `platform`: Informações do sistema operacional e arquitetura.
- `modules.hardware`: Utilizado para operações pesadas assíncronas de identificação de máquina que mantêm cache (`obter_hardware_com_cache` e `coletar_hardware_completo`).
- `time.sleep`: Utilizado em escopos confinados para calcular o delta de bytes lidos e escritos no disco (`obter_metricas_completas`).

## Métodos Disponíveis
**Fluxos Síncronos:**
- `obter_hardware()`: Retorna as infos pesadas base que foram guardadas internamente durante a injeção do objeto (vindo do launcher/inicialização).
- `obter_nivel_qualidade_visual()`: Repassa as infos pesadas para o módulo calcular se o setup é fraco ou forte (determina blur e partículas).
- `obter_metricas_rapidas()`: Rápido e instantâneo, captura apenas `%` da CPU, RAM e freq, sendo essencial para o topo do software (polling do loop de hardware a cada segundo).
- `obter_info_sistema_detalhado()`: Captura listagem de discos e hardware em profundidade de forma on-demand (utilizado na tab principal de setup).
- `obter_metricas_completas()`: Calcula disco, rede e tudo simultaneamente para o modo Hardware Monitor, travando a thread brevemente para calcular o I/O disk delta de `0.5s`.
- `obter_gpu_rapida()`: Checa instantaneamente a GPUtil primária, ignorando erros silenciosamente e passando dados limpos de load e temp (usado no polling de topo de interface).

**Fluxos Assíncronos:**
Essas tarefas delegam funções para o `modules.hardware`, mas a responsabilidade de assincronicidade é do `JobManager` embutido na `PhoenixAPI`.
- `carregar_hardware_cache(progress_callback)`: Varre `WMI` da máquina, guardando em cache. Manda strings de progresso pro callback.
- `forcar_rescan_hardware(progress_callback)`: Ignora o cache local e regera o WMI da máquina.

## Fallbacks
- Ausência de GPU: Funções que retornam uso de GPU ignoram silenciosamente, retornando `"gpu": None` dentro do dicionário JSON.
- Timeout / Sensor indisponível: O framework devolve um array com valores zerados mas que mantém o tipo original (não retornando exceptions na bridge).
- O módulo protege qualquer tentativa de serialização errática formatando ints e floats truncados de maneira limpa nas respostas (ex. `round(..., 1)`).

## Pontos Futuros
- Modularizar `modules/hardware.py` de modo que a própria classificação de nível visual pertença a um domínio independente.
- Desacoplar I/O de disco da chamada de métrica global, passando a utilizar métricas reativas em vez do travamento síncrono por `0.5s`.
- Centralizar telemetria e análise cruzada de thermal throttling para o modo Optimizer.
