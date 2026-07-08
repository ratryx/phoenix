# Feature Specification: Ponto de Restauração Automático

**Feature Branch**: `002-ponto-restauracao-auto`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Antes de qualquer otimização ser aplicada, o sistema deve criar automaticamente um ponto de restauração nativo do Windows via PowerShell (Checkpoint-Computer). O usuário deve ver o progresso e confirmar antes de prosseguir. Se a criação falhar, o sistema deve alertar e perguntar se deseja continuar mesmo assim."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criação e Confirmação do Ponto de Restauração (Priority: P1)

Como usuário do Phoenix Optimizer, quero que o sistema crie automaticamente um ponto de restauração do sistema operacional antes de aplicar qualquer otimização, para que eu tenha a segurança de poder desfazer as alterações caso ocorra algum problema grave no Windows.

**Why this priority**: Crítico para a segurança do sistema do usuário e garantido pelo Princípio II da Constituição do projeto.

**Independent Test**: Pode ser verificado iniciando qualquer otimização e observando o início automático do processo de criação do ponto de restauração, seguido pela barra de progresso e pelo pedido de confirmação.

**Acceptance Scenarios**:

1. **Given** que o usuário solicitou a aplicação de otimizações, **When** o processo é iniciado, **Then** o sistema deve invocar a criação do ponto de restauração nativo do Windows, exibir o progresso na tela e solicitar a confirmação do usuário antes de realmente aplicar as otimizações.
2. **Given** que o ponto de restauração foi criado com sucesso, **When** o usuário confirma o prosseguimento, **Then** o sistema deve iniciar a aplicação das otimizações selecionadas.
3. **Given** que o ponto de restauração foi criado com sucesso, **When** o usuário cancela a operação no prompt de confirmação, **Then** as otimizações não devem ser aplicadas e o sistema deve retornar ao estado anterior de forma segura.

---

### User Story 2 - Tratamento de Falha na Criação do Ponto de Restauração (Priority: P2)

Como usuário do Phoenix Optimizer, quero ser alertado se a criação do ponto de restauração falhar, e poder escolher se desejo continuar com as otimizações mesmo sem essa proteção ou se prefiro abortar o processo.

**Why this priority**: Importante para garantir a autonomia do usuário e lidar com sistemas operacionais onde a restauração de sistema está desativada ou indisponível, sem bloquear completamente o uso se o usuário assumir o risco.

**Independent Test**: Pode ser verificado em um ambiente com a Restauração do Sistema desativada no painel de controle do Windows, iniciando uma otimização e validando se o alerta de falha aparece com as opções de continuar ou abortar.

**Acceptance Scenarios**:

1. **Given** que o sistema de restauração do Windows falhou ou está desativado, **When** o sistema tenta criar o ponto de restauração, **Then** o sistema deve detectar a falha, exibir um alerta explicativo e perguntar explicitamente se o usuário deseja continuar mesmo assim.
2. **Given** o alerta de falha de criação, **When** o usuário responde que deseja continuar, **Then** o sistema deve prosseguir com as otimizações.
3. **Given** o alerta de falha de criação, **When** o usuário responde que deseja abortar, **Then** o sistema deve cancelar a operação e não aplicar nenhuma otimização.

---

### Edge Cases

- **Restauração do Sistema Desativada no Windows**: O Windows por padrão pode ter a Restauração do Sistema desativada para a unidade C:. O sistema deve detectar essa condição de forma amigável e alertar o usuário, instruindo como ativar se necessário.
- **Falta de Privilégios de Administrador**: A criação de pontos de restauração via `Checkpoint-Computer` exige privilégios de administrador. Se o programa não estiver rodando como administrador, deve alertar o usuário.
- **Execução em Modo Não Interativo/CLI Automatizada**: Se o usuário rodar a CLI com uma flag silenciosa (caso implementada no futuro), o sistema deve abortar por padrão se a criação do ponto de restauração falhar, a menos que uma flag de força (`--force`) seja especificada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST disparar automaticamente a criação do ponto de restauração antes de executar qualquer script de otimização de sistema ou alteração de serviço.
- **FR-002**: O sistema MUST exibir visualmente o progresso da criação do ponto de restauração (tanto na GUI quanto na CLI).
- **FR-003**: O sistema MUST solicitar confirmação explícita do usuário após a conclusão (ou falha) do ponto de restauração e antes de aplicar as otimizações.
- **FR-004**: Se o comando de restauração retornar erro ou falhar por qualquer motivo (limite de pontos de restauração diários atingido, serviço desativado, etc.), o sistema MUST interceptar o erro e exibir um aviso claro.
- **FR-005**: O sistema MUST disponibilizar as opções de "Continuar mesmo assim" e "Cancelar" caso ocorra falha na criação.
- **FR-006**: A lógica de detecção, execução e tratamento do ponto de restauração MUST ser centralizada no módulo de lógica de negócios (core) para ser compartilhada de forma idêntica entre a CLI e a GUI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em condições normais (com suporte ativo no Windows), o ponto de restauração é criado e a confirmação é exibida ao usuário sem travar a interface.
- **SC-002**: 100% das tentativas de otimização que não possuem ponto de restauração prévio são precedidas pela rotina de criação de backup do sistema.
- **SC-003**: 100% dos cenários de falha na criação geram um prompt de decisão para o usuário, impedindo a aplicação silenciosa e desprotegida de otimizações.

## Assumptions

- O aplicativo é executado com privilégios de Administrador (necessário para manipulação de serviços e restauração do sistema).
- O comando nativo `Checkpoint-Computer` está disponível no PowerShell do Windows da máquina cliente.
- A descrição/nome do ponto de restauração gerado conterá a identificação do aplicativo, por exemplo: `Phoenix Optimizer - Pré-Otimização`.
