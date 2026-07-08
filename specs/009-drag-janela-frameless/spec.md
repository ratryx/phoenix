# Feature Specification: Correção: Drag da Janela Frameless

**Feature Branch**: `009-drag-janela-frameless`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "A janela pywebview atualmente trava no monitor e não pode ser movida. Implementar drag via JavaScript capturando mousedown na titlebar e chamando função Python que reposiciona a janela."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Movimentação da Janela Personalizada (Priority: P1)

Como usuário da interface gráfica do Phoenix Optimizer, quero poder arrastar a janela do aplicativo clicando e movendo o mouse sobre a barra de título personalizada, para que eu possa posicionar o programa em qualquer monitor ou parte da minha tela de trabalho de forma intuitiva, resolvendo o problema atual onde a janela fica travada em uma posição fixa.

**Why this priority**: Correção de bug de usabilidade essencial. Uma janela que não pode ser movida prejudica gravemente a experiência do usuário e a acessibilidade.

**Independent Test**: Abrir o Phoenix Optimizer em modo GUI, clicar na barra de título superior, manter pressionado e arrastar o mouse. Validar se a janela se move de forma contínua seguindo a velocidade do cursor.

**Acceptance Scenarios**:

1. **Given** que o usuário está com a GUI do Phoenix aberta, **When** ele clica com o botão esquerdo do mouse na barra de título (titlebar) e move o cursor, **Then** o sistema deve atualizar continuamente a posição da janela na tela de forma correspondente ao movimento.
2. **Given** que o usuário solta o botão do mouse (mouseup), **When** o arraste é concluído, **Then** a janela deve permanecer na nova posição e o evento de arraste deve ser encerrado.

---

### User Story 2 - Prevenção de Ações Conflitantes na Barra de Título (Priority: P2)

Como usuário, quero que cliques normais nos botões de fechar, minimizar ou menus contidos na barra de título realizem suas funções originais sem fazer com que a janela se mova acidentalmente, garantindo o comportamento padrão de janelas do Windows.

**Why this priority**: Evita frustração do usuário e interações confusas ao tentar fechar ou minimizar o aplicativo.

**Independent Test**: Clicar no botão "Minimizar" ou "Fechar" na barra de título personalizada e verificar se a ação esperada é executada imediatamente sem que a janela sofra micro-movimentos de reposicionamento na tela.

**Acceptance Scenarios**:

1. **Given** que o cursor está posicionado sobre um botão interativo da barra de título (como fechar ou minimizar), **When** o usuário clica com o mouse, **Then** o evento de clique deve ser consumido pelo botão (realizando a ação correspondente) e a rotina de arraste da janela não deve ser acionada.

---

### Edge Cases

- **Arraste Fora dos Limites da Tela (Off-screen)**: O usuário pode tentar arrastar a janela de forma a ocultá-la completamente fora do monitor. O sistema deve limitar a posição mínima da barra de título para garantir que ela sempre permaneça visível em pelo menos algum monitor ativo do Windows, impedindo que o usuário "perca" a janela de vista.
- **Múltiplos Monitores com Resoluções/DPIs Diferentes**: Ao arrastar a janela de um monitor para outro com DPI ou escala diferentes, o sistema deve manter o arraste fluido e as coordenadas de transição de tela de forma nativa e correta.
- **Micro-arrastes de cliques acidentais**: Se o usuário der um clique simples (mousedown e mouseup rápidos no mesmo ponto), o sistema deve ignorar e não invocar a chamada de API de movimentação, prevenindo pequenas oscilações de pixels da janela.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST responder ao evento de arraste da janela sob a barra de título personalizada (titlebar).
- **FR-002**: A detecção inicial do clique (mousedown) e início do arraste MUST ser implementada no frontend via JavaScript.
- **FR-003**: O JavaScript no frontend MUST invocar uma função exposta pelo backend Python (API da janela) para enviar as coordenadas ou solicitar o reposicionamento físico da janela do pywebview.
- **FR-004**: O arraste de janela MUST rodar com baixo atraso de renderização para garantir movimento fluido (60 FPS ou superior).
- **FR-005**: O sistema MUST isolar elementos clicáveis da barra de título (como botões de controle de janela e links de navegação) para que cliques ou interações nestes elementos específicos não iniciem o arraste da janela.
- **FR-006**: A funcionalidade de arraste de janela customizada MUST se aplicar exclusivamente ao modo gráfico (GUI).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O arraste da janela é iniciado em menos de 50 milissegundos após o clique e movimento inicial do cursor na barra de título.
- **SC-002**: A janela se move com suavidade e sem trepidações visíveis em telas de alta taxa de atualização (144Hz ou superior).
- **SC-003**: 100% dos cliques estáticos na barra de título ou botões de controle de janela não alteram as coordenadas X e Y da janela.

## Assumptions

- O frontend HTML/CSS/JS possui uma barra de título contendo uma classe CSS ou atributo identificador específico (ex: `.titlebar` ou `id="titlebar"`) que demarca a área válida para início de arraste.
- O pywebview fornece métodos nativos na API do Python (como `window.move` ou funções semelhantes de manipulação de janela) que podem ser chamadas a partir da ponte JavaScript.
