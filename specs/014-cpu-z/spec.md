# Feature Specification: CPU-Z (Informações Estáticas do Hardware)

**Feature Branch**: `014-cpu-z`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Informações estáticas detalhadas do hardware. Usa cache da FEATURE 011. Aba isolada, somente GUI. Layout em cards..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acesso Imediato a Dados de Hardware (Priority: P1)

O técnico clica na aba "CPU-Z" e visualiza instantaneamente um raio-x detalhado do hardware do cliente (Processador, Placa-mãe, RAM, GPU, Discos). 

**Why this priority**: É essencial para o técnico saber com o que está lidando antes de tomar decisões sobre upgrades (ex: saber que a RAM é DDR3 1333MHz ou se a placa-mãe tem slot livre).

**Independent Test**: Pode ser testado abrindo o programa, clicando na aba CPU-Z e observando o tempo de carregamento e a correção dos dados exibidos contra uma ferramenta externa (ex: Gerenciador de Tarefas ou CPU-Z real).

**Acceptance Scenarios**:

1. **Given** o cache de hardware da Feature 011 já está populado, **When** o usuário clica na aba CPU-Z, **Then** as informações são exibidas instantaneamente sem tempos de espera.
2. **Given** a aba CPU-Z é renderizada, **Then** as informações estão segmentadas visualmente em Cards (CPU, RAM, Placa-Mãe, GPU, Armazenamento) sem uso de jargões/siglas técnicas obscuras.

---

### User Story 2 - Forçar Atualização e Exportação (Priority: P2)

O técnico trocou uma peça de hardware (ex: colocou mais memória RAM) com o aplicativo aberto. Ele quer forçar o sistema a ler a nova peça e, em seguida, exportar esse "laudo" para o relatório do cliente, provando o upgrade.

**Why this priority**: Complementa a utilidade estática da ferramenta, integrando com o restante do fluxo de atendimento e vendas.

**Independent Test**: Pode ser testado clicando em "Forçar Re-scan", observando o carregamento (spinner temporário) e posteriormente clicando em "Exportar para o Relatório". O próximo relatório gerado deve conter esses dados adicionais.

**Acceptance Scenarios**:

1. **Given** o usuário está na aba CPU-Z, **When** ele clica em "Forçar Re-scan", **Then** o sistema invalida o cache atual (Feature 011), dispara um novo scan completo e atualiza a tela com os novos dados.
2. **Given** os dados estão visíveis, **When** o usuário clica em "Exportar para o Relatório", **Then** o sistema salva temporariamente essas informações no contexto do atendimento atual, e o próximo relatório gerado incluirá essa seção de laudo de hardware.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE possuir uma aba exclusiva na GUI para o CPU-Z.
- **FR-002**: A aba DEVE exibir as seguintes informações do Processador: Nome completo, fabricante, arquitetura, núcleos físicos/threads lógicas, frequência base e boost (MHz), Cache L1/L2/L3, Socket, Stepping e Revisão (se disponíveis via WMI).
- **FR-003**: A aba DEVE exibir as seguintes informações de RAM: Total instalada, tipo (DDR3/DDR4/DDR5), frequência, Slots usados/livres, e Fabricante.
- **FR-004**: A aba DEVE exibir as seguintes informações de Placa-mãe: Fabricante, modelo, chipset, versão e data do BIOS.
- **FR-005**: A aba DEVE exibir as seguintes informações de GPU: Nome, VRAM, versão do driver e data do driver.
- **FR-006**: A aba DEVE exibir as informações de Armazenamento para cada disco: Modelo, tipo (SSD/HDD/NVMe), capacidade e saúde S.M.A.R.T resumida.
- **FR-007**: A aba DEVE recuperar e renderizar dados instantaneamente a partir do Cache de Hardware (Feature 011).
- **FR-008**: A aba DEVE incluir um botão "Forçar Re-scan" que limpa o cache e aciona a releitura dos dados, usando o padrão `job_id` + `polling` (Feature 012).
- **FR-009**: A aba DEVE incluir um botão "Exportar para o Relatório", que registra os dados na variável de estado do atendimento atual para serem inclusos na exportação (HTML/TXT).
- **FR-010**: O design DEVE organizar os dados em cards separados por categoria e usar texto legível (ex: "Frequência" em vez de "Clk", "Arquitetura" em vez de "Arch").

### Key Entities

- **HardwareSnapshot**: Registro detalhado e estático dos componentes do computador (provido pelo cache).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O carregamento da aba e renderização dos dados a partir de cache válido ocorre em menos de 100ms.
- **SC-002**: O relatório exportado inclui a seção de laudo de hardware formatada corretamente sem quebrar os layouts de tabela existentes.
- **SC-003**: Nenhum jargão estritamente interno do WMI (ex: Win32_Processor) é exibido na UI.

## Assumptions

- Algumas informações (como geração DDR, ou Cache L1 exato) podem não estar disponíveis perfeitamente via WMI em hardwares muito antigos ou placas genéricas. O sistema deve preencher com "Desconhecido" sem quebrar o layout.
- Essa ferramenta é focada 100% na GUI, não impactando a experiência da CLI.
