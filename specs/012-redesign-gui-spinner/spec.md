# Feature Specification: Redesign GUI + Correção Definitiva do Spinner

**Feature Branch**: `012-redesign-gui-spinner`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Redesign GUI + Correção Definitiva do Spinner. Solução obrigatória — padrão job_id + polling..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interface Responsiva durante Operações Pesadas (Priority: P1)

O técnico clica para executar a Rotina Completa (ou outra operação demorada). O spinner de carregamento aparece e gira fluidamente, sem congelar, e a interface continua responsiva (pode ser arrastada, minimizada), até que a operação seja concluída e o resultado exibido.

**Why this priority**: A interface atual trava (congela) durante operações pesadas devido à limitação síncrona da bridge do pywebview. Isso passa a sensação de que o programa "travou" ou "crashou", arruinando a experiência do usuário.

**Independent Test**: Clicar em "Rotina Completa" e verificar se a janela pode ser movida e se o spinner de CSS gira sem interrupções (60fps) durante todo o processo.

**Acceptance Scenarios**:

1. **Given** o usuário está na tela inicial, **When** ele clica em iniciar uma limpeza profunda, **Then** o backend inicia o processo em uma thread separada, o frontend exibe um spinner animado e faz polling do status, e a janela permanece 100% responsiva a redimensionamento ou arrasto.
2. **Given** o processo em background termina, **When** o frontend faz o próximo polling e recebe "done", **Then** o spinner desaparece e a tela de resultados é exibida.

---

### User Story 2 - Nova Estrutura de Navegação (Sidebar e Abas) (Priority: P2)

O técnico acessa o programa e vê uma barra lateral (sidebar) intuitiva, contendo abas (Dashboard, HWMonitor, CPU-Z, Otimizações, Logs) que permitem alternar rapidamente entre as ferramentas sem voltar para um "Menu Principal" engessado.

**Why this priority**: Prepara o terreno arquitetural da GUI para receber as features 013 (HWMonitor) e 014 (CPU-Z). O layout atual não suporta múltiplas telas isoladas de forma elegante.

**Independent Test**: Clicar em diferentes ícones na barra lateral e verificar se a área de conteúdo central muda instantaneamente para a aba correspondente.

**Acceptance Scenarios**:

1. **Given** o usuário abriu o programa, **When** ele clica no ícone de "Otimizações" na sidebar, **Then** a área principal transita suavemente para a tela de otimizações, mantendo a sidebar visível.
2. **Given** o usuário está na aba "Logs", **When** ele clica na aba "Dashboard", **Then** ele retorna à tela inicial.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE adotar um padrão de `job_id` + `polling` para qualquer função Python que leve mais de 100ms para executar (ex: scans, limpezas, otimizações).
- **FR-002**: O backend Python DEVE encapsular operações longas em `threading.Thread`, registrar o estado em um dicionário global `_tarefas[job_id]`, e retornar o `job_id` imediatamente para o frontend.
- **FR-003**: O backend Python DEVE expor um método `verificar_tarefa(job_id)` que retorna o status atual ("running", "done", "error") e o resultado/erro correspondente.
- **FR-004**: O frontend JS DEVE chamar a função inicial, receber o `job_id` e usar `setInterval` (ex: 500ms) para chamar `verificar_tarefa(job_id)` até obter conclusão.
- **FR-005**: O sistema DEVE implementar um layout de janela principal (layout.html/css) contendo uma Sidebar fixa à esquerda (ou topo) e uma área de conteúdo dinâmico (Main Content).
- **FR-006**: A Sidebar DEVE conter links/ícones de navegação para: Início (Rotina), Otimizações Avulsas, HWMonitor (Slot), CPU-Z (Slot), e Histórico.
- **FR-007**: O design visual DEVE manter a identidade "glassmorphism dark" atual, refinando espaçamentos e reduzindo poluição visual.

### Key Entities

- **BackgroundJob**: Registro da tarefa em execução no backend, contendo ID, Status, e Resultado (se concluído).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O spinner de carregamento CSS nunca perde quadros (drops frames) ou congela, mantendo animação constante a ~60fps durante qualquer operação longa.
- **SC-002**: A janela do aplicativo permanece arrastável (movimentável pelo usuário na área de trabalho) durante a execução de ferramentas.
- **SC-003**: Transição entre abas ocorre em menos de 100ms.

## Assumptions

- O frontend utilizará HTML/CSS/JS puro ou framework leve já presente; o polling será implementado via `setInterval` ou `requestAnimationFrame`.
- Funções rápidas (ex: retornar versão do app, maximizar janela) continuam sendo chamadas de forma síncrona.
