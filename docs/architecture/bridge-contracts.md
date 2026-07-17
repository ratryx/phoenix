# Contratos da Bridge (Python -> JavaScript)

Este documento mapeia todos os métodos públicos da classe `PhoenixAPI` (localizada em `modules/gui/api.py`) acessíveis pelo JavaScript através do objeto `pywebview.api`. Estes contratos são críticos para o funcionamento do frontend e não devem ser quebrados durante refatorações.

> **Nota sobre Tratamento de Erros:** O contrato para operações assíncronas garante que exceções internas do Python nunca vazem tracebacks, caminhos locais ou variáveis de ambiente para a interface. O frontend recebe apenas uma estrutura sanitizada como `{"ok": false, "erro": "Mensagem amigável", "detalhe": "Detalhe seguro"}`, enquanto as informações técnicas ficam restritas aos logs nativos. O mesmo contrato sanitizado se aplica para erros de serialização JSON e conflitos de concorrência. Jobs expirados e inexistentes possuem um contrato próprio unificado: `{"status": "not_found"}`.

## Sistema Base & Janela

> **Nota Arquitetural:** Os métodos de controle de janela (arrasto, minimizar e fechar) estão isolados no `WindowController`. A `PhoenixAPI` apenas roteia as chamadas para este controlador interno sem manter estado visual nativo.

| Método | Tipo | Parâmetros | Retorno / Estrutura | Efeitos Colaterais / Notas | Risco de Regressão |
|--------|------|------------|---------------------|----------------------------|--------------------|
| `verificar_tarefa` | Síncrono | `job_id: str` | `{"status": str, "resultado": any, "progresso": int, "mensagem": str}` ou `{"status": "not_found"}` | Acesso apenas em memória (`_tarefas`). | **Crítico**. Base do polling do frontend. |
| `iniciar_drag` | Síncrono | `start_mouse_x: int, start_mouse_y: int, start_win_x: int, start_win_y: int` | `None` | Habilita flag de arrasto. | Baixo. Interface frameless. |
| `mover_janela` | Síncrono | `current_mouse_x: int, current_mouse_y: int` | `None` | Move a janela no Windows. | Baixo. Interface frameless. |
| `parar_drag` | Síncrono | N/A | `None` | Desabilita flag de arrasto. | Baixo. Interface frameless. |
| `minimizar_janela` | Síncrono | N/A | `None` | Minimiza janela usando pywebview. | Baixo. |
| `fechar_janela` | Síncrono | N/A | `None` | Fecha janela usando pywebview. | Baixo. |

## Hardware & Ambiente

> **Nota Arquitetural:** Todos os métodos deste escopo (que antes usavam chamadas de bibliotecas do sistema diretamente na bridge) agora delegam integralmente para o `HardwareService`, garantindo abstração completa. Os payloads retornados ao JS são montados por este serviço e os contratos abaixo continuam rigorosamente inalterados.

| Método | Tipo | Parâmetros | Retorno / Estrutura | Efeitos Colaterais / Notas | Risco de Regressão |
|--------|------|------------|---------------------|----------------------------|--------------------|
| `obter_hardware` | Síncrono | N/A | `dict` (hardware salvo no estado da API) | Nenhum. | Baixo. |
| `obter_nivel_qualidade_visual` | Síncrono | N/A | `str` ("alto", "medio", "baixo") | Chama `hardware.classificar_capacidade_hardware`. | Baixo. Usado para partículas/efeitos no CSS. |
| `carregar_hardware_cache` | Async (job_id) | N/A | `job_id`. Result: `{"ok": bool, "hardware": dict}` | Chama `hardware.obter_hardware_com_cache`. Único com suporte nativo a progresso reportado ao frontend. | Alto. Tela inicial e rodape dependem disso. |
| `forcar_rescan_hardware` | Async (job_id) | N/A | `job_id`. Result: `{"ok": bool, "hardware": dict}` | Chama `hardware.coletar_hardware_completo`. | Médio. |
| `obter_metricas_rapidas` | Síncrono | N/A | `{"ok": bool, "cpu_percent": float, "ram_percent": float, "ram_disponivel_gb": float, "cpu_freq_mhz": float}` | Bloqueia por 100ms (`psutil`). | Médio. Usado no polling da página inicial. |
| `obter_info_sistema_detalhado` | Síncrono | N/A | `{"ok": bool, "sistema": dict, "cpu": dict, "ram": dict, "discos": list, "gpus": list}` | Bloqueia minimamente, varre hardware real. | Baixo. |
| `obter_metricas_completas` | Síncrono | N/A | `{"ok": bool, "cpu": dict, "ram": dict, "disco": dict, "gpu": dict}` | Bloqueia por 500ms+ (`time.sleep` para delta de I/O disco). | Alto. Usado no HWMonitor, bloqueia a thread de bridge temporariamente. |
| `obter_gpu_rapida` | Síncrono | N/A | `{"ok": bool, "gpu": dict}` ou `{"ok": False, "gpu": None}` | Usa `GPUtil`. | Baixo. |

## Diagnóstico & Otimização

| Método | Tipo | Parâmetros | Retorno / Estrutura | Efeitos Colaterais / Notas | Risco de Regressão |
|--------|------|------------|---------------------|----------------------------|--------------------|
| `obter_diagnostico` | Async (job_id) | N/A | `job_id`. Result: `{"ok": bool, "dados": dict}` | Varre disco, rede, ram, cpu via `diagnostico.coletar_diagnostico_silencioso`. | Médio. Renderiza a página inteira de Diagnóstico. |
| `executar_limpeza` | Async (job_id) | N/A | `job_id`. Result: `{"ok": True, "espaco_liberado_mb": float}` | Chama `limpeza.executar_limpeza_completa`. Apaga arquivos reais no disco. *Privilégio Admin recomendado*. | Alto. Destrutivo. |
| `criar_ponto_restauracao` | Async (job_id) | N/A | `job_id`. Result: dependente de `otimizacao.criar_ponto_restauracao` | Interage com WMI/PowerShell. *Requer Privilégio Admin*. | Alto. Destrutivo. |
| `executar_otimizacao_geral` | Async (job_id) | N/A | `job_id`. Result: `{"ok": True}` | Altera registro e configurações. *Requer Privilégio Admin*. | Alto. Destrutivo. |
| `executar_otimizacao_gaming` | Async (job_id) | `resetar_rede: bool` | `job_id`. Result: `{"ok": True}` | Altera registro, energia. *Requer Privilégio Admin*. | Alto. Destrutivo. |
| `otimizar_disco` | Async (job_id) | N/A | `job_id`. Result: `{"ok": True, "saida": ...}` | Executa trim/desfragmentação. *Requer Privilégio Admin*. | Médio. Destrutivo. |
| `listar_inicializacao` | Síncrono | N/A | `{"ok": bool, "saida": ...}` ou `{"ok": False, "erro": str}` | Lê chaves de registro. | Baixo. |
| `analisar_startup` | Async (job_id) | N/A | `job_id`. Result: `{"ok": True, "entradas": list}` | Analisa impacto da inicialização. | Baixo. |
| `liberar_memoria_standby` | Async (job_id) | N/A | `job_id`. Result: `{"ok": bool, "mensagem": str}` | Usa RamMap/Windows API. *Requer Privilégio Admin*. | Médio. |
| `executar_rotina_completa` | Async (job_id) | `nome_cliente: str` | `job_id`. Result: `{"ok": True, "id_atendimento": str, "antes": dict, "depois": dict, "espaco_liberado_mb": float, "relatorio_txt": str}` | Executa Diagnóstico, Limpeza, Otimização e Snapshot de log sequencialmente. *Requer Privilégio Admin*. | **Crítico**. Rotina mais complexa da aplicação. |

## Serviços

| Método | Tipo | Parâmetros | Retorno / Estrutura | Efeitos Colaterais / Notas | Risco de Regressão |
|--------|------|------------|---------------------|----------------------------|--------------------|
| `listar_servicos` | Async (job_id) | N/A | `job_id`. Result: `{"ok": True, "servicos": list}` | Lista serviços via powershell. | Médio. |
| `desativar_servico` | Async (job_id) | `nome_servico: str` | `job_id`. Result: `{"ok": bool}` | Para e desativa serviço real. *Requer Privilégio Admin*. | Médio. Destrutivo. |
| `ativar_servico` | Async (job_id) | `nome_servico: str` | `job_id`. Result: `{"ok": bool}` | Ativa e inicia serviço real. *Requer Privilégio Admin*. | Médio. Destrutivo. |

## Atendimento, Logs & Portable

| Método | Tipo | Parâmetros | Retorno / Estrutura | Efeitos Colaterais / Notas | Risco de Regressão |
|--------|------|------------|---------------------|----------------------------|--------------------|
| `iniciar_atendimento` | Síncrono | `nome_cliente: str` | `{"id_atendimento": str}` | Cria ID na sessão da API. | Baixo. |
| `obter_clientes_portable` | Síncrono | N/A | `{"ok": bool, "portable": bool, "clientes": list}` | Acessa arquivos do pen drive. | Baixo. |
| `selecionar_cliente` | Síncrono | `nome: str` | `{"ok": bool, "cliente": str}` ou `{"ok": False, "erro": str}` | Salva `meta.json` no pen drive. | Baixo. |
| `remover_cliente_portable`| Síncrono | `id_cliente: str`| `{"ok": bool, "erro": str}` | Apaga cliente do pen drive. | Baixo. Destrutivo em portable. |
| `obter_modo_portable` | Síncrono | N/A | `{"portable": bool, "cliente_ativo": str}` | Lê estado global `IS_PORTABLE`. | Baixo. |
| `obter_historico` | Síncrono | N/A | `{"ok": bool, "atendimentos": list}` | Lê a pasta de logs. | Baixo. |

## Contrato Específico: executar_rotina_completa

A rotina completa é a operação mais complexa do Phoenix Optimizer e possui um contrato rígido que deve ser preservado.

*   **Método:** `PhoenixAPI.executar_rotina_completa(nome_cliente: str = "")`
*   **Parâmetros:**
    *   `nome_cliente` (str): Nome do cliente para registro no relatório. Opcional (string vazia por padrão).
*   **Retorno Inicial (Síncrono):**
    *   `{"job_id": str}`
*   **Payload Final (Assíncrono via `verificar_tarefa`):**
    *   `ok` (bool): `True` se a rotina foi concluída com sucesso.
    *   `id_atendimento` (str): UUID do atendimento gerado (`logs.gerar_id_atendimento()`).
    *   `antes` (dict): Dados do diagnóstico obtidos *antes* da limpeza/otimização via `diagnostico.coletar_diagnostico_silencioso()`.
    *   `depois` (dict): Dados do diagnóstico obtidos *após* a limpeza/otimização via `diagnostico.coletar_diagnostico_silencioso()`.
    *   `espaco_liberado_mb` (float): Quantidade de espaço em disco liberado, convertido para Megabytes (duas casas decimais).
    *   `relatorio_txt` (str): Caminho absoluto para o arquivo de texto gerado contendo o sumário do atendimento.
*   **Mensagens de Erro (em caso de falha capturada pelo JobManager):**
    *   Retorna `{"ok": False, "erro": str, "detalhe": str}` padronizado pelo job.
*   **Progresso:**
    *   Não há e nunca houve emissão de callbacks de progresso granular. O frontend exibe apenas um spinner de progresso global neutro ("Executando rotina completa...").
*   **Efeitos Colaterais Esperados (Ordem Estrita):**
    1.  Criação de `id_atendimento`.
    2.  Leitura de diagnóstico prévio.
    3.  Salvar snapshot JSON do diagnóstico prévio e registro de log inicial.
    4.  Execução da limpeza destrutiva de disco.
    5.  Execução de otimizações de performance em registro/configurações.
    6.  Leitura de diagnóstico posterior.
    7.  Salvar snapshot JSON do diagnóstico posterior e registro de log final.
    8.  Exportação de arquivo de texto TXT.
*   **Nota sobre Ponto de Restauração:** Na arquitetura atual, o *frontend* (`app.js`) invoca e aguarda `criar_ponto_restauracao` explicitamente *antes* de invocar `executar_rotina_completa`. O fluxo contido no backend *não* engatilha o rollback por conta própria.
