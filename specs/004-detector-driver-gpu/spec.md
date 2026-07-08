# Feature Specification: Detecção de Driver de GPU Desatualizado

**Feature Branch**: `004-detector-driver-gpu`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Ler versão atual do driver via nvidia-smi (NVIDIA) e wmic (AMD). Comparar com versão mais recente disponível no site oficial. Nunca instalar automaticamente — apenas informar e exibir link para a página oficial de downloads. Suportar NVIDIA e AMD. Intel integrada é opcional. Incluir no relatório."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificação de Atualização da GPU (Priority: P1)

Como usuário do Phoenix Optimizer, quero que o sistema detecte se o driver da minha placa de vídeo (NVIDIA ou AMD) está desatualizado em comparação com a versão oficial mais recente, para que eu possa garantir a estabilidade e o melhor desempenho nos jogos.

**Why this priority**: Drivers de vídeo desatualizados são uma das causas mais comuns de baixo desempenho e falhas em jogos.

**Independent Test**: Executar a ferramenta em um sistema com driver de GPU desatualizado e confirmar se ela exibe o status indicando que há uma nova versão disponível.

**Acceptance Scenarios**:

1. **Given** que o usuário possui uma placa NVIDIA ou AMD e o driver instalado é anterior ao mais recente, **When** a detecção é iniciada, **Then** o sistema deve exibir a versão instalada, a versão mais recente disponível no mercado e um aviso de que está desatualizado.
2. **Given** que o driver da GPU do usuário já está na versão mais recente, **When** a detecção é iniciada, **Then** o sistema deve mostrar uma confirmação de que o driver está atualizado.

---

### User Story 2 - Direcionamento para Instalação Manual (Priority: P2)

Como usuário do Phoenix Optimizer, quero que o sistema me mostre um link direto para a página de downloads oficiais do fabricante para atualizar o driver da minha GPU manualmente, e nunca faça alterações automáticas ou silenciosas, para que eu mantenha total controle sobre o que é instalado no meu sistema.

**Why this priority**: Evitar falhas críticas no sistema operacional causadas por instalações automáticas mal-sucedidas ou incompatíveis de drivers de vídeo.

**Independent Test**: Clicar na recomendação de atualização do driver na interface gráfica e validar se um navegador padrão é aberto no site oficial de drivers do respectivo fabricante.

**Acceptance Scenarios**:

1. **Given** que o driver da GPU NVIDIA está desatualizado, **When** o aviso é apresentado, **Then** o sistema deve exibir um botão/link para a página de drivers da NVIDIA.
2. **Given** que o driver da GPU AMD está desatualizado, **When** o aviso é apresentado, **Then** o sistema deve exibir um botão/link para a página de drivers da AMD.
3. **Given** qualquer cenário de atualização, **When** o sistema detecta que o driver precisa de atualização, **Then** ele NUNCA deve iniciar um processo automático de download silencioso ou instalação em background de drivers.

---

### User Story 3 - Registro de Informações de Vídeo no Relatório (Priority: P2)

Como usuário do Phoenix Optimizer, quero ver o status e as versões dos drivers de GPU detalhados no relatório gerado pelo aplicativo, para que eu possa compartilhar ou arquivar esse registro de otimização.

**Why this priority**: Permite que o usuário e técnicos validem rapidamente se o driver foi identificado como um possível gargalo de desempenho durante a análise.

**Independent Test**: Executar uma verificação de driver e gerar o relatório para confirmar se a marca da GPU, a versão do driver e a necessidade de atualização constam no relatório.

**Acceptance Scenarios**:

1. **Given** que a otimização ou diagnóstico foi executado, **When** o relatório final é gerado, **Then** as informações de "GPU, Driver Instalado, Driver Recente, Status de Atualização" devem estar descritas na seção de hardware do relatório.

---

### Edge Cases

- **Sem Conexão com a Internet**: Se o usuário rodar o Phoenix Optimizer offline, o sistema não conseguirá ler a versão mais recente do site oficial. O sistema deve exibir a versão do driver local e exibir amigavelmente a mensagem: "Não foi possível verificar atualizações (sem conexão de internet)."
- **Placas de Vídeo Integradas Intel**: Placas integradas Intel são opcionais. Se uma GPU Intel for detectada como primária, o sistema deve exibir o modelo e o driver instalado, mas pode marcar a verificação de atualizações online como "Não suportado para GPUs integradas Intel nesta versão".
- **Sistemas com Múltiplas GPUs (Ex: Notebooks Híbridos com Intel + NVIDIA)**: O sistema deve listar ambas as GPUs no diagnóstico, mas realizar a verificação de drivers e atualizações exclusivamente para a GPU dedicada (NVIDIA ou AMD).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST ler o modelo da placa de vídeo e identificar se o fabricante é NVIDIA ou AMD.
- **FR-002**: O sistema MUST obter a versão do driver instalado localmente usando o utilitário `nvidia-smi` para placas NVIDIA, e via consultas WMI (`Get-CimInstance Win32_VideoController` ou `wmic path win32_videocontroller get driverversion`) para placas AMD.
- **FR-003**: O sistema MUST comparar a versão detectada localmente com a versão estável mais recente do mercado.
- **FR-004**: O sistema MUST expor o link oficial de download de drivers correspondente:
  - NVIDIA: Página de busca de drivers oficial da NVIDIA.
  - AMD: Página de busca de drivers oficial da AMD.
- **FR-005**: O sistema MUST proibir terminantemente o download automático ou instalação autônoma de drivers de GPU.
- **FR-006**: O sistema MUST tratar falhas de rede de forma graciosa, sem abortar a rotina de execução ou travar a tela do usuário.
- **FR-007**: As informações da GPU detectada e do driver MUST ser incluídas no relatório gerado em `%PROGRAMDATA%\PhoenixOptimizer\logs\`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos testes offline, o sistema exibe o driver local sem erros de runtime ou travamentos.
- **SC-002**: A comparação de versões é completada em menos de 3 segundos quando há acesso à internet estável.
- **SC-003**: A aplicação nunca realiza chamadas de instalação silenciosa ou scripts de atualização automatizada de drivers.

## Assumptions

- O Phoenix Optimizer consultará as versões de driver mais recentes por meio de uma lista/arquivo de consulta atualizada hospedada de forma estática no repositório do projeto, ou através de chamadas seguras e rápidas de API, para evitar lentidão e problemas de bloqueio (scrapers de páginas diretas da NVIDIA/AMD costumam quebrar facilmente devido a alterações de layout).
- A GPU ativa de maior poder computacional (dedicada) será a preferida para a verificação de drivers em sistemas híbridos.
