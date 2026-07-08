# Feature Specification: Verificação S.M.A.R.T. de Saúde do Disco

**Feature Branch**: `003-verificacao-smart-disco`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Leitura dos atributos S.M.A.R.T. via wmic ou smartctl. Sem instalar nada externo se possível. A interface deve mostrar apenas 3 estados: Saudável / Atenção / Crítico. Traduzir os atributos técnicos em linguagem simples para o cliente. Incluir no relatório antes/depois."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualização Rápida e Simplificada da Saúde do Disco (Priority: P1)

Como usuário do Phoenix Optimizer, quero ver rapidamente a integridade dos meus discos de armazenamento (SSD/HDD) classificados de forma simples (Saudável, Atenção ou Crítico), para que eu saiba se o meu hardware está seguro ou se há risco iminente de perda de dados.

**Why this priority**: Funcionalidade principal de diagnóstico de hardware que previne o usuário de aplicar otimizações em discos fisicamente comprometidos.

**Independent Test**: Pode ser verificado abrindo a aba de diagnósticos/discos e confirmando se o status de saúde do disco principal é exibido sob uma das 3 classificações.

**Acceptance Scenarios**:

1. **Given** que o disco principal está em perfeito estado de funcionamento, **When** o diagnóstico é executado, **Then** o sistema deve exibir o status como "Saudável" na tela.
2. **Given** que o disco principal apresenta sinais iniciais de desgaste (como setores realocados baixos), **When** o diagnóstico é executado, **Then** o sistema deve exibir o status como "Atenção" e listar o motivo em termos simples.
3. **Given** que o disco principal relata falha preditiva iminente de hardware (alerta WMI PredictFailure ativo), **When** o diagnóstico é executado, **Then** o sistema deve exibir o status como "Crítico", emitir um alerta visual destacado e sugerir o backup dos dados imediatamente.

---

### User Story 2 - Tradução de Atributos Técnicos para Linguagem Simples (Priority: P2)

Como usuário leigo, quero que os problemas encontrados nos atributos S.M.A.R.T. sejam explicados em português claro, em vez de ver códigos hexadecimais ou jargões técnicos complexos (como "Reallocated Sectors Count" ou "Spin Retry Count"), para que eu entenda o que realmente está acontecendo com meu disco.

**Why this priority**: Melhora a usabilidade e a acessibilidade da ferramenta para usuários não técnicos.

**Independent Test**: Simular retornos de atributos S.M.A.R.T. com falha (mock) e verificar se o texto de explicação técnica é substituído por descrições amigáveis como "Desgaste de memória física" ou "Problema na inicialização do disco".

**Acceptance Scenarios**:

1. **Given** um disco com setores realocados presentes, **When** o usuário expande os detalhes da saúde do disco, **Then** o sistema deve exibir uma mensagem amigável, por exemplo: "Desgaste natural: Alguns blocos de escrita originais falharam e foram substituídos por reservas (Setores Realocados)."
2. **Given** um disco com altas taxas de erro de leitura, **When** os detalhes são exibidos, **Then** o sistema deve traduzir para: "Dificuldade de leitura física: O disco está precisando tentar ler os arquivos mais de uma vez (Erros de Leitura)."

---

### User Story 3 - Inclusão do Diagnóstico no Relatório (Priority: P2)

Como usuário do Phoenix Optimizer, quero que o status de saúde do meu disco antes e depois da otimização seja registrado no relatório gerado pelo sistema, servindo como registro e comprovante do estado físico do meu computador.

**Why this priority**: Essencial para a rastreabilidade e histórico de modificações do sistema do cliente.

**Independent Test**: Executar o processo de otimização completo e abrir o arquivo de relatório gerado para validar a existência da seção "Saúde do Disco (S.M.A.R.T.)" contendo os dados pré e pós-otimização.

**Acceptance Scenarios**:

1. **Given** que o processo de otimização foi concluído, **When** o relatório final (HTML/TXT) é gerado, **Then** ele deve incluir o status de integridade dos discos capturado antes do início e após o término da otimização.

---

### Edge Cases

- **Controladores RAID/NVMe Específicos que Ocultam S.M.A.R.T.**: Algumas controladoras de disco em notebooks ou arranjos RAID podem bloquear a leitura do WMI ou smartctl. O sistema deve capturar a exceção de leitura nula de forma limpa e exibir: "Status S.M.A.R.T. indisponível para este controlador".
- **Discos Externos/USB Conectados**: O sistema deve priorizar o disco onde o Windows está instalado (unidade do sistema C:) e listar secundariamente outros discos internos. Unidades USB externas podem ser ignoradas por padrão ou listadas separadamente para evitar ruído.
- **Incompatibilidade com o comando `wmic`**: O Windows 11 está depreciando o utilitário de linha de comando `wmic`. O sistema deve usar WMI através de chamadas PowerShell/WMI nativas (como `Get-WmiObject` ou `Get-CimInstance`) como fallback primário caso o binário `wmic` não esteja disponível.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST realizar a leitura dos atributos S.M.A.R.T. dos discos de armazenamento principais do computador.
- **FR-002**: O sistema MUST tentar realizar a leitura utilizando componentes nativos do Windows (PowerShell CIM/WMI ou CLI `wmic`) sem requerer download de executáveis de terceiros.
- **FR-003**: O sistema MUST mapear o resultado do status do disco para exatamente um destes três estados simplificados: "Saudável", "Atenção" ou "Crítico".
- **FR-004**: O sistema MUST ter um dicionário interno para tradução dos principais atributos críticos (Ex: ID 05 - Reallocated Sectors, ID 0A - Spin Retry, ID B8 - End-to-End Error, ID C5 - Current Pending Sector, ID C6 - Uncorrectable Sector) para descrições simplificadas em português.
- **FR-005**: O sistema MUST registrar o estado de saúde lido na inicialização e o estado de saúde ao término no arquivo de relatório consolidado (`%PROGRAMDATA%\PhoenixOptimizer\logs\`).
- **FR-006**: A leitura do S.M.A.R.T. MUST ser rápida e não travar a linha de execução principal por mais de 2 segundos. Se demorar mais, deve rodar de forma assíncrona com indicador de carregamento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos sistemas compatíveis, o diagnóstico do disco é carregado em menos de 1.5 segundos.
- **SC-002**: Zero jargões puramente técnicos ou códigos de erro brutos (como raw values hexadecimais) são exibidos de forma isolada na tela principal, garantindo a visualização amigável de alertas.
- **SC-003**: O relatório de otimização gerado armazena com precisão as medições antes e depois de cada ciclo.

## Assumptions

- O Windows expõe os dados de S.M.A.R.T. de forma correta e sem bloqueios de driver para o disco de sistema principal.
- Discos SSD modernos que expõem apenas a porcentagem de vida útil restante via NVMe serão mapeados adequadamente para os 3 estados (Ex: Vida útil > 80% = Saudável; 20% a 80% = Atenção; < 20% ou falha preditiva = Crítico).
