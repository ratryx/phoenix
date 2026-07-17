# Feature Specification: Diagnóstico de Status das Otimizações

**Feature Branch**: `010-diagnostico-status-otimizacoes`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Verificar se as otimizações já aplicadas estão realmente ativas no sistema. Não confiar no histórico — consultar o Windows diretamente."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificar Estado das Otimizações (Priority: P1)

O técnico quer saber se as otimizações que ele aplicou (ou que foram aplicadas em visita anterior) ainda estão ativas no sistema do cliente. Em vez de confiar no histórico de logs, o programa consulta diretamente o Windows (registro, serviços, configurações) e mostra o estado real de cada otimização.

**Why this priority**: É o núcleo da feature — sem esta verificação em tempo real, a feature não tem razão de existir. O técnico precisa de confiança de que o que ele aplicou continua valendo após reinicializações, atualizações do Windows ou alterações do próprio usuário.

**Independent Test**: Pode ser testado rodando a verificação após aplicar qualquer otimização e comparando o resultado com o que o Windows realmente reporta via PowerShell/Registro.

**Acceptance Scenarios**:

1. **Given** o técnico aplicou otimizações no atendimento anterior, **When** ele abre o diagnóstico de status, **Then** o programa consulta o Windows diretamente e exibe o estado real de cada item (ativo/inativo) com indicador visual verde ou vermelho.
2. **Given** o Windows Update reverteu o plano de energia para "Equilibrado" após reinicialização, **When** o técnico executa a verificação, **Then** o item "Plano de energia" aparece como inativo (vermelho) com a informação de que está em "Equilibrado" ao invés de "Alto Desempenho".
3. **Given** todas as otimizações estão ativas, **When** o técnico executa a verificação, **Then** todos os itens aparecem verdes e nenhum botão "Reaplicar" individual é destacado.

---

### User Story 2 - Reaplicar Otimização Individual (Priority: P2)

Quando um item específico está inativo, o técnico pode reaplicar apenas aquele item sem precisar rodar toda a otimização novamente.

**Why this priority**: Complementa o diagnóstico com ação direta — sem ela, o técnico sabe que algo está inativo mas precisa ir ao menu principal para corrigir, perdendo tempo.

**Independent Test**: Pode ser testado alterando manualmente uma chave de registro para "desativado", verificando que o diagnóstico mostra vermelho, clicando "Reaplicar" naquele item, e verificando que ficou verde.

**Acceptance Scenarios**:

1. **Given** o item "Game Mode" está inativo, **When** o técnico clica em "Reaplicar" ao lado desse item, **Then** a otimização correspondente é aplicada e o status atualiza para ativo (verde) sem afetar os outros itens.
2. **Given** a reaplicação de um item requer privilégio de administrador e o programa não está rodando como administrador, **When** o técnico tenta reaplicar, **Then** o programa exibe mensagem de erro informando a necessidade de rodar como administrador.

---

### User Story 3 - Reaplicar Todas as Otimizações Inativas (Priority: P2)

Um botão "Reaplicar Todos" permite corrigir todas as otimizações que estiverem inativas de uma só vez.

**Why this priority**: Mesmo nível de P2 pois é uma conveniência direta da reaplicação individual — economiza tempo quando múltiplos itens foram revertidos (comum após atualizações do Windows).

**Independent Test**: Pode ser testado manualmente desativando 3+ itens, clicando "Reaplicar Todos", e verificando que todos voltaram ao estado ativo.

**Acceptance Scenarios**:

1. **Given** 4 de 7 otimizações estão inativas, **When** o técnico clica em "Reaplicar Todos", **Then** apenas as 4 inativas são reaplicadas e todos os itens ficam verdes.
2. **Given** todas as otimizações já estão ativas, **When** o técnico clica em "Reaplicar Todos", **Then** o programa informa que não há nada a reaplicar e nenhuma ação é executada.

---

### Edge Cases

- O que acontece quando uma chave de registro não existe (nunca foi criada porque a otimização nunca foi aplicada)? O item deve aparecer como "inativo" sem erro.
- Como o sistema lida quando o plano de energia "Alto Desempenho" não está disponível (foi removido pelo OEM)? Deve mostrar o estado real e informar qual plano está ativo.
- O que acontece se o serviço consultado não existir no sistema (ex: versões diferentes do Windows)? Deve marcar como "Não encontrado" em vez de erro.
- O que acontece se a reaplicação falhar parcialmente durante o "Reaplicar Todos"? Deve reportar quais itens foram reaplicados com sucesso e quais falharam.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE consultar diretamente o Windows (registro, PowerShell, serviços) para determinar o estado real de cada otimização, sem confiar em histórico ou logs internos.
- **FR-002**: O sistema DEVE verificar os seguintes itens de otimização:
  - Plano de energia ativo (verificar se é "Alto Desempenho" ou "Ultimate Performance")
  - Modo de Jogo do Windows (chave de registro AllowAutoGameMode/AutoGameModeEnabled)
  - Agendador de GPU por hardware (chave de registro HwSchMode)
  - Overlay do Xbox Game Bar (chave de registro AppCaptureEnabled)
  - Serviços desativados pelo Phoenix (verificar status atual de cada serviço da lista segura)
  - SysMain/Prefetch (verificar estado do serviço)
  - Efeitos visuais (verificar UserPreferencesMask no registro)
- **FR-003**: O sistema DEVE exibir cada item com indicador visual claro: verde (✅ = ativo/otimizado) ou vermelho (❌ = inativo/não otimizado).
- **FR-004**: O sistema DEVE oferecer um botão "Reaplicar" ao lado de cada item individual que estiver inativo.
- **FR-005**: O sistema DEVE oferecer um botão "Reaplicar Todos" que aplica todas as otimizações atualmente inativas de uma vez.
- **FR-006**: O sistema DEVE estar disponível tanto no modo CLI (lista textual com símbolos ✅/❌) quanto no modo GUI (cards visuais).
- **FR-007**: O sistema DEVE seguir o princípio Dual-Interface CLI/GUI — a lógica de verificação e reaplicação deve estar em módulo compartilhado.
- **FR-008**: O sistema DEVE criar um ponto de restauração antes de reaplicar otimizações (conforme Princípio II da Constituição).
- **FR-009**: O sistema DEVE registrar as ações de reaplicação no log de atendimento quando um atendimento estiver ativo.

### Key Entities

- **ItemOtimizacao**: Representa uma otimização verificável — contém identificador, descrição amigável, estado atual (ativo/inativo/não encontrado), e a função de reaplicação associada.
- **ResultadoDiagnostico**: Contém a lista completa de ItemOtimizacao verificados, com totais de ativos/inativos/não encontrados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A verificação completa de todos os itens de otimização é concluída em menos de 10 segundos.
- **SC-002**: O estado reportado para cada item corresponde 100% ao estado real do Windows (verificável por consulta PowerShell manual).
- **SC-003**: A reaplicação individual de um item inativo altera o estado do item para ativo em menos de 5 segundos.
- **SC-004**: O "Reaplicar Todos" corrige todos os itens inativos em uma única operação, sem requerer ações adicionais do técnico.
- **SC-005**: Tanto CLI quanto GUI exibem os mesmos itens e estados, sem discrepância entre os modos.

## Assumptions

- O programa roda com privilégios de administrador para poder consultar e alterar registros do sistema.
- As chaves de registro verificadas são as mesmas que o módulo `otimizacao.py` utiliza para aplicar otimizações (não há divergência entre o que é aplicado e o que é verificado).
- Serviços do Windows que não existem em determinada versão do Windows (ex: serviços removidos no Windows 11) são tratados como "Não encontrado" sem gerar erro.
- A feature não verifica otimizações que foram aplicadas por outros programas — apenas o que o Phoenix Optimizer pode aplicar.
