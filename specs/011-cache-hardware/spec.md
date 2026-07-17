# Feature Specification: Cache de Hardware com Invalidação Automática

**Feature Branch**: `011-cache-hardware`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Salvar resultado do scan de hardware em JSON para não repetir o processo a cada abertura. Invalidação automática por mudança de hardware ou expiração de 30 dias."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Abertura Instantânea com Cache Válido (Priority: P1)

Na segunda vez que o programa é aberto no mesmo computador (sem mudanças de hardware), os dados de hardware são carregados instantaneamente do cache, sem refazer o scan completo que normalmente leva vários segundos.

**Why this priority**: É o valor principal da feature — a abertura lenta do programa é o primeiro ponto de fricção na experiência do técnico, especialmente em hardware mais fraco onde consultas WMI/PowerShell demoram.

**Independent Test**: Pode ser testado abrindo o programa duas vezes seguidas e medindo o tempo da segunda abertura (deve ser significativamente mais rápido).

**Acceptance Scenarios**:

1. **Given** o programa foi aberto anteriormente neste computador e gerou um cache, **When** o programa é aberto novamente sem mudanças de hardware, **Then** os dados de hardware são carregados do cache em menos de 1 segundo, sem chamar WMI/PowerShell para scan completo.
2. **Given** o programa é aberto pela primeira vez neste computador (sem cache), **When** o scan é concluído, **Then** o resultado é salvo automaticamente no arquivo de cache para uso futuro.

---

### User Story 2 - Invalidação Automática por Mudança de Hardware (Priority: P1)

Se o técnico trocar um componente (ex: upgrade de RAM, troca de GPU) e abrir o programa, o sistema detecta a divergência e refaz o scan automaticamente, sem mostrar dados desatualizados.

**Why this priority**: Mesmo nível de P1 porque dados incorretos de hardware são piores que dados lentos — se o cache mostrar a GPU antiga após um upgrade, o diagnóstico perde credibilidade.

**Independent Test**: Pode ser testado simulando mudança de hardware (editando manualmente o cache JSON) e verificando que o programa detecta a divergência e refaz o scan.

**Acceptance Scenarios**:

1. **Given** o cache indica 16GB de RAM, **When** o programa detecta que o sistema agora possui 32GB, **Then** o cache é descartado, um scan completo é executado, e o novo resultado é salvo.
2. **Given** o cache indica uma GPU NVIDIA RTX 3060, **When** o programa detecta uma GPU diferente, **Then** o scan completo é refeito automaticamente.
3. **Given** o cache expirou (mais de 30 dias desde a última atualização), **When** o programa é aberto, **Then** o scan completo é refeito independentemente de mudança de hardware.

---

### User Story 3 - Forçar Re-scan Manual (Priority: P2)

O técnico pode forçar um novo scan de hardware a qualquer momento, descartando o cache existente, para garantir dados 100% atualizados.

**Why this priority**: Segurança do técnico — mesmo com invalidação automática, situações inesperadas (ex: troca de periférico que não altera CPU/RAM/GPU) podem justificar um rescan manual.

**Independent Test**: Pode ser testado clicando "Forçar Re-scan" e verificando que o programa refaz a coleta completa e atualiza o cache.

**Acceptance Scenarios**:

1. **Given** o cache é válido e atual, **When** o técnico clica em "Forçar Re-scan", **Then** o cache é descartado, um scan completo é executado, e o novo resultado substitui o cache anterior.

---

### Edge Cases

- O que acontece se o arquivo de cache estiver corrompido (JSON inválido)? O programa deve descartar o cache silenciosamente e refazer o scan.
- O que acontece se o programa não tiver permissão de escrita no diretório de cache? Deve funcionar normalmente sem cache (modo degradado), sem travar.
- O que acontece se o computador tiver múltiplas GPUs e apenas uma for trocada? A comparação deve detectar a mudança e invalidar.
- O que acontece se o arquivo de cache for deletado manualmente pelo usuário? O programa deve refazer o scan na próxima abertura como se fosse a primeira vez.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE salvar o resultado completo do scan de hardware em arquivo de cache no diretório padrão de dados do programa.
- **FR-002**: O cache DEVE incluir no mínimo: modelo de CPU, número de núcleos, RAM total, modelo(s) de GPU, VRAM, modelo da placa-mãe, versão do BIOS, e lista de discos presentes.
- **FR-003**: Na abertura do programa, o sistema DEVE comparar os campos de validação (modelo CPU, RAM total, modelo(s) GPU) entre o cache e uma consulta rápida ao sistema.
- **FR-004**: Se qualquer campo de validação divergir, o sistema DEVE descartar o cache e executar um scan completo automaticamente.
- **FR-005**: Se todos os campos de validação coincidirem e o cache tiver menos de 30 dias, o sistema DEVE carregar os dados do cache sem refazer o scan completo.
- **FR-006**: O cache DEVE expirar automaticamente após 30 dias mesmo sem mudança de hardware, forçando um novo scan.
- **FR-007**: O sistema DEVE oferecer um botão/opção "Forçar Re-scan" sempre visível para o técnico descartar o cache manualmente.
- **FR-008**: O sistema DEVE tratar cache corrompido (JSON inválido, campos faltantes) silenciosamente, descartando e refazendo o scan.
- **FR-009**: O sistema DEVE funcionar normalmente sem cache (modo degradado) quando não tiver permissão de escrita no diretório de cache.
- **FR-010**: O sistema DEVE seguir o princípio Dual-Interface CLI/GUI — a lógica de cache é compartilhada entre ambos os modos.

### Key Entities

- **CacheHardware**: Estrutura de dados contendo os resultados do scan, timestamp de criação, e campos de validação rápida (CPU modelo, RAM total, GPU modelo).
- **ValidacaoCache**: Resultado da comparação entre campos de validação do cache e do sistema atual — determina se o cache é válido ou precisa ser refeito.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A abertura do programa com cache válido carrega os dados de hardware em menos de 1 segundo (vs. 5-15 segundos sem cache, dependendo do hardware).
- **SC-002**: Mudanças de CPU, RAM ou GPU são detectadas automaticamente em 100% dos casos testados, sem mostrar dados desatualizados.
- **SC-003**: O cache expira corretamente após 30 dias, forçando um novo scan na próxima abertura.
- **SC-004**: Cache corrompido ou inacessível nunca causa travamento ou erro visível — o programa simplesmente refaz o scan.

## Assumptions

- O diretório `%PROGRAMDATA%\PhoenixOptimizer\cache\` é utilizável para armazenamento do cache (mesmo diretório raiz dos logs, já validado como gravável).
- A consulta rápida para validação (CPU + RAM + GPU modelo) é significativamente mais rápida que o scan completo — tipicamente < 1 segundo vs. 5-15 segundos.
- Os campos de validação escolhidos (CPU, RAM, GPU) são suficientes para detectar as mudanças de hardware mais comuns; periféricos (mouse, teclado, monitor) não invalidam o cache.
- O tamanho do arquivo de cache é desprezível (< 10KB em JSON).
