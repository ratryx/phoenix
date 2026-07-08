# Feature Specification: Modo Gamer Simplificado

**Feature Branch**: `008-modo-gamer-simplificado`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Ativar com um clique. Ao ativar: 1. Detectar automaticamente processos de jogos em execução e elevar prioridade para High (nunca Realtime). 2. Liberar Standby Memory. 3. Fechar a interface do Phoenix completamente, mantendo apenas um processo mínimo em background (menos de 1MB RAM, zero CPU em idle) para permitir reversão. Ao desativar (reabrindo o Phoenix): Reverter prioridade dos processos ao normal. Ícone na system tray para reabrir enquanto minimizado. NUNCA usar prioridade Realtime. NUNCA suspender processos de sistema."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ativação do Modo Gamer com Um Clique (Priority: P1)

Como usuário jogador do Phoenix Optimizer, quero ativar o Modo Gamer com um único clique para que o sistema detecte meus jogos abertos, eleve a prioridade deles para "High", limpe a memória Standby do Windows e feche a interface pesada do aplicativo para economizar recursos físicos de RAM e CPU.

**Why this priority**: Funcionalidade principal de otimização ativa para jogos, focada em maximizar o desempenho e liberar o máximo de recursos de hardware possíveis.

**Independent Test**: Iniciar um jogo (ex: `Minecraft.exe` ou `Valorant.exe`), clicar no botão "Ativar Modo Gamer" no Phoenix e validar se:
1. A janela do Phoenix é completamente fechada.
2. A prioridade do processo do jogo no Gerenciador de Tarefas do Windows foi alterada para "High".
3. A memória em cache/Standby diminuiu significativamente.
4. Um ícone do Phoenix aparece na Área de Notificação (System Tray).

**Acceptance Scenarios**:

1. **Given** que um jogo conhecido ou processo de jogo está rodando, **When** o usuário clica em "Ativar Modo Gamer", **Then** o sistema deve elevar a prioridade do jogo para "High" (Alta), limpar a memória cache/Standby do Windows, fechar a interface do Phoenix e carregar o ícone na system tray rodando sob um processo de background extremamente leve.
2. **Given** a ativação do Modo Gamer, **When** o sistema otimiza as prioridades de CPU, **Then** ele NUNCA deve alterar a prioridade de nenhum processo para "Realtime" (Tempo Real) e NUNCA deve suspender ou alterar prioridades de processos nativos críticos do Windows.

---

### User Story 2 - Desativação e Restauração de Estado (Priority: P1)

Como usuário, quero desativar o Modo Gamer clicando duas vezes no ícone da system tray ou executando novamente o atalho do Phoenix Optimizer, para que o sistema reverta as prioridades dos meus jogos de volta ao nível "Normal" e restaure a interface gráfica principal do Phoenix.

**Why this priority**: Permite que o sistema operacional volte ao seu fluxo de trabalho normal e o usuário possa utilizar outros aplicativos com prioridades padrão sem intervenção manual.

**Independent Test**: Com o Modo Gamer ativo, dar um duplo clique no ícone da bandeja do sistema (System Tray) ou reabrir o Phoenix pelo atalho de Desktop e verificar se a prioridade do jogo retorna para "Normal", a janela principal do Phoenix reabre e o processo em background é encerrado.

**Acceptance Scenarios**:

1. **Given** que o Modo Gamer está ativo, **When** o usuário escolhe desativar (dando duplo clique no ícone do tray ou reabrindo o Phoenix), **Then** o sistema deve restaurar a prioridade de todos os processos que foram elevados para "Normal" (ou o valor original do sistema), fechar o processo mínimo do tray e reabrir a interface gráfica completa do Phoenix Optimizer.

---

### Edge Cases

- **Fechamento do Jogo Durante o Modo Gamer**: Se o usuário fechar o jogo voluntariamente enquanto o Modo Gamer estiver ativo: o sistema deve simplesmente detectar a ausência do processo e, quando o Modo Gamer for desativado, ignorar os processos que já não existem mais no Windows de forma segura.
- **Detecção de Jogos de Plataformas Comuns**: O sistema deve implementar uma lógica de detecção heurística/de caminhos para identificar se um processo é um jogo (ex: checar se o processo está em pastas como `SteamLibrary`, `Epic Games`, `XboxGames`, `Origin Games`, ou se possui consumo intenso de GPU 3D, ou uma lista de nomes comuns). Processos do sistema e navegadores de internet devem ser explicitamente ignorados.
- **Falta de Memória Física para a System Tray**: O processo de background para o ícone de notificação na system tray deve ser construído sem dependências pesadas de GUI (como carregar o renderizador CEF ou WebView2). Ele deve ser uma rotina em Python pura e extremamente leve que consuma estritamente menos de 1MB de RAM e 0% de CPU em modo ocioso.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST fornecer um botão único de ativação do Modo Gamer Simplificado na interface gráfica.
- **FR-002**: O sistema MUST elevar a prioridade de processos identificados como jogos para a prioridade de CPU "High" (Alta). O sistema NUNCA deve aplicar a prioridade "Realtime" (Tempo Real).
- **FR-003**: O sistema MUST ignorar e NUNCA alterar prioridades ou suspender processos críticos do Windows (ex: `explorer.exe`, `svchost.exe`, `lsass.exe`, `wininit.exe`).
- **FR-004**: O sistema MUST invocar chamadas de sistema ou APIs do Windows para liberar a memória Standby (cache de arquivos não modificados em RAM) no momento da ativação.
- **FR-005**: O sistema MUST encerrar por completo a janela principal e os processos pesados de renderização (WebView2) do Phoenix Optimizer ao ativar o Modo Gamer.
- **FR-006**: O sistema MUST manter em execução um processo mínimo na system tray do Windows, consumindo menos de 1MB de RAM e 0% de CPU em idle, para monitorar e aguardar o sinal de restauração.
- **FR-007**: Ao desativar o Modo Gamer, o sistema MUST retornar a prioridade dos processos alterados para "Normal", encerrar o processo leve do tray e reabrir a interface gráfica principal do aplicativo.
- **FR-008**: Esta funcionalidade MUST ser desenvolvida de forma exclusiva para a GUI, não possuindo representação equivalente na CLI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O consumo de memória RAM do processo em background minimalista (tray daemon) não excede 1.0 MB em repouso.
- **SC-002**: A ocupação de CPU do daemon do tray é de exatamente 0.0% em idle.
- **SC-003**: Zero processos do sistema operacional Windows sofrem suspensão ou alteração de prioridades de escalonamento de CPU durante o processo de elevação.

## Assumptions

- O aplicativo é executado com privilégios administrativos elevados (necessário para redefinir prioridades de processos de outros proprietários e para limpar a memória cache/Standby do Windows).
- O usuário possui uma GPU dedicada ou integrada instalada com drivers funcionais.
- A detecção de jogos usará heurísticas seguras baseadas no diretório de instalação do executável e no uso de aceleradores gráficos.
