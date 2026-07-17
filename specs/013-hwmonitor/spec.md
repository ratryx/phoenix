# Feature Specification: HWMonitor

**Feature Branch**: `013-hwmonitor`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Monitoramento em tempo real de todos os sensores do sistema. Aba isolada, somente GUI. Usa padrão job_id. Atualização a cada 2s..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualização de Sensores em Tempo Real (Priority: P1)

O técnico, visando identificar gargalos de performance ou superaquecimento, acessa a aba "HWMonitor". A tela exibe mostradores circulares (gauges) ou barras preenchendo dinamicamente, acompanhados de gráficos de linha desenhando-se ao vivo, atualizando os dados (temperatura, uso de CPU/GPU, etc) a cada 2 segundos, sem travar o aplicativo.

**Why this priority**: É a essência da feature de monitoramento em tempo real. Identificar superaquecimento é essencial antes de aplicar otimizações ou diagnosticar problemas.

**Independent Test**: Pode ser testado executando um stress test (ex: Prime95, FurMark) em segundo plano enquanto se observa a aba HWMonitor — as temperaturas e uso devem subir nos gráficos em tempo real.

**Acceptance Scenarios**:

1. **Given** a aba HWMonitor está aberta, **When** passam-se 2 segundos, **Then** os dados visuais na tela (CPU, RAM, GPU, Disco, Rede) se atualizam para refletir a nova leitura.
2. **Given** a temperatura da CPU ultrapassa 80°C, **When** os dados são atualizados, **Then** o indicador visual correspondente muda para amarelo (Atenção).
3. **Given** o usuário transita da aba HWMonitor para outra aba, **When** a aba de destino carrega, **Then** o polling em tempo real é interrompido, poupando recursos de CPU.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE possuir uma aba exclusiva na GUI para o HWMonitor.
- **FR-002**: O sistema DEVE monitorar e exibir em tempo real (atualização a cada 2 segundos) as seguintes métricas:
  - CPU: Uso total (%), Uso por núcleo (%), Frequência atual por núcleo (MHz), Temperatura (°C), Potência estimada (W - se disponível).
  - GPU: Uso (%), VRAM usada/total (MB), Temperatura (°C), Clock atual (MHz).
  - RAM: Usada/Total (GB), Disponível (GB), % de uso.
  - Armazenamento (Disco): Velocidade de leitura/escrita (MB/s), % de uso de I/O.
  - Rede: Velocidade de Upload/Download atual (MB/s).
- **FR-003**: O sistema DEVE utilizar fallback de métodos para captura térmica (Ex: wmi, tools nativas).
- **FR-004**: O frontend DEVE implementar gráficos de linha para registrar o histórico dos últimos 60 segundos de temperatura (CPU e GPU).
- **FR-005**: O sistema visual DEVE usar cores indicativas: Verde (normal), Amarelo (atenção), Vermelho (crítico).
- **FR-006**: O sistema DEVE aplicar os seguintes limiares de cor: CPU >80°C (amarelo), >95°C (vermelho); GPU >85°C (amarelo), >100°C (vermelho).
- **FR-007**: A requisição de dados ao backend DEVE obrigatoriamente utilizar o padrão assíncrono (`job_id` + `polling` implementado na Feature 012), para evitar bloqueio da interface gráfica.

### Key Entities

- **SystemSensorsData**: Estrutura contendo todas as métricas capturadas em um dado instante (`t`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O painel HWMonitor atualiza todos os seus sensores na GUI em um intervalo máximo de 2 segundos, sem engasgos ou congelamentos de interface (steady ~60fps nas animações CSS).
- **SC-002**: O impacto de CPU do próprio polling do HWMonitor não excede 5% de uso em processadores de entrada (ex: Core i3 antigo).
- **SC-003**: Ao trocar de aba, o tráfego de polling do frontend cessa imediatamente (0 requests).

## Assumptions

- A captura de temperatura via WMI pode não funcionar em todas as placas-mãe sem privilégios de administrador ou sem drivers ACPI/WMI específicos. O sistema tentará os métodos sem quebrar.
- A aba HWMonitor existirá apenas na versão GUI; a versão CLI não será impactada (permanece estática).
