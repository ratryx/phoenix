# Feature Specification: Monitoramento em Tempo Real

**Feature Branch**: `006-monitoramento-tempo-real`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Atualização a cada 2 segundos via loop Python → JS. Dados a monitorar: CPU (uso total, uso por núcleo, frequência atual, temperatura), RAM (uso total, disponível, em uso), GPU (uso, VRAM usada/total, temperatura, clock), Disco (velocidade de leitura e escrita em tempo real), Rede (velocidade de upload e download em tempo real). Temperatura de CPU via wmi. GPU via nvidia-smi. Esta aba existe somente na GUI, não na CLI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monitoramento de CPU e RAM (Priority: P1)

Como usuário da interface gráfica do Phoenix Optimizer, quero acompanhar em tempo real o uso do meu processador (total e por núcleo), sua frequência de clock, temperatura e o consumo de memória RAM atualizados a cada 2 segundos, para que eu possa avaliar o impacto de jogos ou tarefas pesadas na máquina.

**Why this priority**: Métricas cruciais de integridade e gargalo de sistema que são consultadas com maior frequência pelos usuários.

**Independent Test**: Abrir a interface gráfica na aba de Monitoramento e verificar se os indicadores numéricos e gráficos de CPU (total e por núcleo) e RAM são atualizados de forma contínua no intervalo de 2 segundos.

**Acceptance Scenarios**:

1. **Given** que o usuário abriu a aba de Monitoramento, **When** o ciclo de atualização de 2 segundos ocorre, **Then** o sistema deve atualizar os dados de carga total da CPU, uso por núcleo lógico individual, frequência em GHz, temperatura em °C e o uso de memória RAM (Total, Em Uso e Livre).

---

### User Story 2 - Monitoramento de GPU, Disco e Rede (Priority: P2)

Como usuário gamer do Phoenix Optimizer, quero visualizar em tempo real o uso da minha placa de vídeo (utilização do chip, consumo e total de VRAM, temperatura e clock), além da atividade de escrita/leitura do meu disco e taxas de transferência da minha rede, para identificar se há algum componente limitando a minha jogabilidade.

**Why this priority**: Ajuda a identificar gargalos comuns em jogos (como falta de VRAM ou gargalos de leitura de disco/latência de rede).

**Independent Test**: Abrir a aba de Monitoramento durante o download de um jogo ou teste de estresse de GPU e validar se os valores de atividade de rede, disco e GPU respondem dinamicamente e de forma coerente.

**Acceptance Scenarios**:

1. **Given** que a placa de vídeo (NVIDIA/AMD) está em execução, **When** a aba de monitoramento está ativa, **Then** os dados de temperatura, clock do núcleo, uso do processador gráfico e ocupação da VRAM devem ser exibidos de forma atualizada.
2. **Given** que há transferências ocorrendo na rede e gravação no disco, **When** a interface atualiza, **Then** as velocidades de upload/download de rede e de leitura/escrita do disco devem ser calculadas e mostradas em MB/s ou KB/s correspondentes.

---

### Edge Cases

- **Ausência de Sensor de Temperatura da CPU via WMI**: Alguns computadores (especialmente máquinas virtuais ou processadores rodando em certas placas-mãe sem suporte a drivers WMI específicos de fabricante) não expõem a temperatura da CPU através do WMI tradicional. O sistema deve capturar a exceção de consulta nula e mostrar "N/D" (Não Disponível) na temperatura de CPU, continuando a coletar e atualizar o uso de CPU, RAM e outras métricas sem interrupções ou travamentos.
- **Placas de Vídeo Não NVIDIA**: O utilitário `nvidia-smi` funciona apenas para placas de vídeo NVIDIA. Se o usuário possuir placa AMD ou Intel dedicada, o sistema deve utilizar fallbacks alternativos (como consultas WMI de performance da placa de vídeo) ou, se a leitura falhar, exibir "N/D" nos campos de temperatura e clock específicos da GPU de forma graciosa.
- **Inatividade de Rede/Desconexão**: Em caso de perda de conexão ou adaptador de rede inativo, as taxas de upload e download devem mostrar "0 KB/s" de forma limpa, sem estourar erros de divisão por zero ou exceções na lógica de loop.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST estabelecer um loop de comunicação assíncrona entre o backend Python e o frontend JavaScript que atualize as informações a cada 2 segundos.
- **FR-002**: O sistema MUST obter o uso total da CPU, a porcentagem de uso de cada núcleo lógico individualmente, a frequência do processador atualizada e a temperatura do processador (esta última via chamadas WMI nativas do Windows).
- **FR-003**: O sistema MUST obter os dados de memória RAM: capacidade total do sistema, quantidade de memória livre/disponível e total em uso ativo pelo sistema operacional.
- **FR-004**: O sistema MUST coletar estatísticas da GPU dedicada principal (utilização geral, total de VRAM ocupada e disponível, temperatura em °C e clock do núcleo de vídeo). A temperatura e clock de placas NVIDIA devem preferencialmente usar chamadas ao `nvidia-smi`.
- **FR-005**: O sistema MUST mensurar as velocidades de transferência de dados de leitura e escrita do disco de sistema em tempo real.
- **FR-006**: O sistema MUST mensurar as taxas de tráfego de rede (velocidade de upload e download) considerando a soma de todas as placas de rede ativas.
- **FR-007**: A aba de monitoramento e todo o seu processamento gráfico e loop de dados MUST existir exclusivamente na interface gráfica (GUI), não gerando processamento de loop em background quando o usuário estiver utilizando a interface de terminal (CLI).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O ciclo de atualização dos dados na GUI é executado com uma frequência estável de 2.0s ± 0.2s.
- **SC-002**: O consumo de CPU adicional gerado pela rotina de medição no loop Python quando a aba está aberta é inferior a 3% do processador total do usuário.
- **SC-003**: A transição de abas na GUI suspende o loop de requisições de monitoramento no backend Python para economizar recursos do sistema quando a aba de monitoramento não estiver visível.

## Assumptions

- O monitoramento em tempo real é executado apenas quando a GUI está aberta e com a respectiva aba selecionada e visível pelo usuário.
- O WMI do Windows está configurado e funcional para consultas do Namespace `root\wmi` (como `MSAcpi_ThermalZoneTemperature` ou contadores de performance equivalentes fornecidos pelo fabricante da placa-mãe).
