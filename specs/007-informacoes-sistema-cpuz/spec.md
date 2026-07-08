# Feature Specification: Aba de Informações do Sistema

**Feature Branch**: `007-informacoes-sistema-cpuz`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Informações estáticas carregadas uma vez ao abrir a aba. Dados a exibir: CPU (modelo completo, arquitetura, núcleos/threads, cache L1/L2/L3, frequência base e boost), RAM (total, tipo DDR4/DDR5, frequência, slots usados/livres), Placa-mãe (fabricante, modelo, versão do BIOS), GPU (modelo, VRAM, driver instalado). Fonte dos dados: wmi + subprocess + wmic. Esta aba existe somente na GUI, não na CLI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consulta Detalhada de Processador e Memória RAM (Priority: P1)

Como usuário da interface gráfica do Phoenix Optimizer, quero abrir uma aba específica para visualizar informações estáticas e detalhadas sobre a minha CPU (modelo completo, arquitetura, núcleos, threads, caches L1/L2/L3 e frequências de clock) e minha memória RAM (tamanho, tipo DDR4/DDR5, frequência de clock ativo e uso de slots), para ter um diagnóstico técnico do meu hardware sem necessitar do Gerenciador de Tarefas ou aplicativos de terceiros como o CPU-Z.

**Why this priority**: Ajuda o usuário a entender as especificações físicas do computador imediatamente ao planejar otimizações ou upgrades.

**Independent Test**: Clicar na aba "Informações do Sistema" na GUI e verificar se todos os campos de CPU e RAM são carregados e exibidos de forma legível e sem atraso visível.

**Acceptance Scenarios**:

1. **Given** que o usuário abriu a aba de Informações do Sistema, **When** os dados são requisitados pela primeira vez, **Then** o sistema deve realizar uma consulta única aos componentes de hardware do Windows e exibir o nome comercial exato do processador (Ex: `Intel Core i7-12700K` ou `AMD Ryzen 5 5600X`), arquitetura, quantidade de núcleos/threads, capacidade dos caches e clocks de operação, além da capacidade, tecnologia (DDR4/DDR5, etc.) e slots livres de RAM.

---

### User Story 2 - Consulta Detalhada da Placa-Mãe e Placa de Vídeo (Priority: P2)

Como usuário, quero visualizar as especificações de modelo da minha placa-mãe, fabricante, versão atual do BIOS instalada e os dados da minha GPU (modelo, VRAM física instalada e driver ativo) na mesma tela, para facilitar a busca por atualizações de firmware e compatibilidade.

**Why this priority**: Essencial para diagnósticos avançados e para identificar se o computador está rodando uma versão antiga de BIOS que afeta a estabilidade dos drivers de vídeo ou desempenho geral.

**Independent Test**: Abrir a aba de Informações do Sistema e validar a exibição dos dados corretos da placa-mãe (Ex: `ASUSTeK COMPUTER INC.`, modelo `PRIME B450M-GAMING`) e detalhes da GPU.

**Acceptance Scenarios**:

1. **Given** que o Windows expõe os metadados da placa-mãe e da GPU, **When** o usuário abre a aba de Informações do Sistema, **Then** os dados de fabricante da placa-mãe, modelo, BIOS, modelo da placa de vídeo, VRAM em GB e driver instalado devem ser exibidos de forma estruturada.

---

### Edge Cases

- **Mapeamento Incorreto de Tipo de Memória (DDR4/DDR5) pelo SMBIOS**: Algumas placas-mãe mais antigas ou chips de RAM genéricos não retornam o valor correto do tipo de memória nas chaves numéricas do WMI (`Win32_PhysicalMemory`). O sistema deve ter um mapeamento atualizado (conforme as tabelas SMBIOS mais recentes) para traduzir os códigos retornados para strings amigáveis (como "DDR4" ou "DDR5"). Se o código for desconhecido, exibir o valor retornado junto à palavra "Desconhecido" (Ex: "Tipo: Desconhecido (34)").
- **Virtualização/Hipervisores (Máquinas Virtuais)**: Em VMs, placa-mãe, caches de CPU e slots de memória RAM física podem retornar valores nulos ou vazios. O sistema deve tratar essas strings nulas de forma elegante substituindo-as por "Virtualizado" ou "Não disponível".
- **Sem privilégios de consulta**: Se o subsistema WMI do Windows estiver corrompido, a tela deve reportar que os serviços de informação estão indisponíveis e sugerir a reparação do WMI no Windows, sem que isso derrube a aplicação.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST carregar os dados de hardware uma única vez de forma estática ao abrir a aba, mantendo as informações em cache para evitar chamadas de subprocesso repetitivas e lentidão na interface.
- **FR-002**: O sistema MUST obter e exibir as especificações detalhadas da CPU: nome do modelo comercial, arquitetura de bits (x86, x64, ARM), número de núcleos físicos, número de processadores lógicos (threads), tamanhos de cache L1, L2 e L3, frequência de clock base e frequência de clock boost estimada.
- **FR-003**: O sistema MUST identificar os detalhes de memória RAM: capacidade total do sistema em GB, tipo de tecnologia de memória (DDR3, DDR4, DDR5, etc.), frequência atual do barramento em MHz e quantidade total de slots físicos disponíveis versus slots ocupados no hardware.
- **FR-004**: O sistema MUST ler dados de identificação da placa-mãe: nome do fabricante, modelo da placa-mãe e versão da BIOS instalada.
- **FR-005**: O sistema MUST obter dados estáticos de vídeo: nome do modelo da GPU ativa principal, quantidade total de VRAM dedicada e versão atualizada do driver instalado.
- **FR-006**: Esta aba de informações completas do sistema MUST ser desenvolvida exclusivamente para a interface gráfica (GUI), não sendo necessário replicar a mesma riqueza de dados estáticos complexos na interface de terminal (CLI).
- **FR-007**: A coleta de informações de hardware MUST ser efetuada via comandos nativos em Python que invoquem consultas WMI locais, `wmic` e comandos de subprocessos (como `powershell Get-CimInstance`), sendo proibida a dependência de instalações ou downloads de instaladores/binários externos proprietários.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O tempo necessário para coletar e renderizar a tela de informações estáticas de hardware na primeira visualização da aba é menor que 1.5 segundos.
- **SC-002**: A interface exibe com precisão as unidades de medida corretas (ex: GB para RAM/VRAM, MHz/GHz para clocks, KB/MB para cache).
- **SC-003**: 100% dos dados ausentes ou não relatados pelo Windows em ambientes virtualizados são tratados sem gerar exceções não capturadas no backend Python.

## Assumptions

- O Windows expõe os dados de hardware padrão através do repositório CIM/WMI e de utilitários como `wmic`.
- O Phoenix Optimizer executará as consultas de hardware de forma assíncrona no backend Python, evitando congelar a renderização da interface web da GUI durante o tempo de espera do carregamento.
