# Feature Specification: Windows GUI Validation

**Feature Branch**: `001-validate-gui-windows`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Validação da GUI no Windows nativo (pywebview)..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Executar a GUI sem console visível (Priority: P1)
O usuário deseja abrir o otimizador no modo gráfico dando dois cliques no executável, e a interface visual deve aparecer sem que uma janela preta do console (Prompt de Comando) fique aberta em segundo plano.
* **Why this priority**: Experiência do usuário (UX) profissional e limpa, essencial para um software desktop Windows moderno.
* **Independent Test**: Compilar o executável no Windows, dar dois cliques nele e verificar se a GUI abre com sucesso e se nenhuma janela de console preta é exibida.
* **Acceptance Scenarios**:
  1. **Given** o executável `launcher.exe` compilado, **When** o usuário executa o arquivo via duplo clique no Windows Explorer, **Then** a janela gráfica do Phoenix Optimizer é exibida e nenhuma janela de console do Windows (cmd.exe/powershell.exe) é aberta ou permanece visível.

---

### User Story 2 - Comunicação Bidirecional e Navegação da GUI (Priority: P1)
O usuário interage com a interface gráfica e espera que as ações (cliques em botões) executem as rotinas em Python, e que os resultados das rotinas em Python sejam renderizados de volta na GUI. Além disso, a navegação entre todas as 8 páginas da GUI deve funcionar fluidamente.
* **Why this priority**: A interface é inútil se não conseguir se comunicar com a lógica de negócios em Python que realiza o diagnóstico e otimização.
* **Independent Test**: Abrir a GUI no Windows, clicar nos botões que acionam rotinas Python de teste (ex: detecção de hardware) e verificar se as informações aparecem na tela, e navegar pelas 8 páginas.
* **Acceptance Scenarios**:
  1. **Given** a GUI aberta no Windows, **When** o usuário clica em botões de navegação, **Then** a interface navega corretamente pelas 8 páginas sem travamentos ou erros de console/script.
  2. **Given** a GUI aberta, **When** o usuário clica em um botão que dispara uma ação em Python, **Then** a rotina Python é executada e seu retorno/resultado é exibido corretamente na interface JS.
  3. **Given** a janela da GUI no modo frameless (sem bordas nativas), **When** o usuário arrasta a barra superior personalizada, **Then** a janela se move de forma fluida pela tela.

---

### Edge Cases

* **Sem WebView2 instalado**: O que acontece se o computador do usuário não tiver o Microsoft WebView2 Runtime instalado? A aplicação deve exibir uma mensagem de erro amigável ao usuário instruindo como instalar ou instalar automaticamente.
* **Execução CLI via Prompt de Comando**: O executável único é compilado como aplicação de GUI (`--noconsole`). Quando executado a partir de um terminal (Prompt de Comando ou PowerShell), a aplicação deve usar a API Win32 (`AttachConsole`) para anexar-se ao console do processo pai, permitindo a saída de texto interativa no terminal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O executável compilado final MUST iniciar a interface gráfica (GUI) baseada em `pywebview` sem exibir uma janela do console do Windows (Prompt de Comando) em segundo plano quando iniciado por duplo clique.
- **FR-002**: A comunicação de JavaScript para Python (JS -> Python) MUST funcionar perfeitamente, permitindo que cliques e eventos na página HTML chamem métodos expostos na classe Python.
- **FR-003**: A comunicação de Python para JavaScript (Python -> JS) MUST funcionar perfeitamente, permitindo que o backend Python envie dados e atualize elementos do DOM da página HTML em tempo real.
- **FR-004**: A funcionalidade de arrastar a janela (drag) customizada (frameless window) MUST operar sem atrasos ou travamentos na interface.
- **FR-005**: A navegação entre as 8 páginas existentes da interface MUST ser validada e livre de erros de carregamento ou scripts JavaScript.
- **FR-006**: O executável compilado MUST suportar execução do modo CLI e, quando executado a partir de um terminal no Windows, deve usar `AttachConsole` para exibir a saída de texto interativa diretamente no terminal atual, sem abrir janelas extras.

### Key Entities

- **Launcher**: O ponto de entrada principal (`launcher.py`) responsável por identificar o ambiente operacional, ler argumentos de linha de comando para determinar o modo de uso (CLI vs GUI) e instanciar a interface adequada.
- **GUI Bridge**: A ponte de comunicação entre Python e o JavaScript da página web, expondo métodos do Python para o frontend e executando chamadas de JS.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das chamadas de funções JS para Python e vice-versa devem ser executadas com latência imperceptível (< 50ms) em ambiente local.
- **SC-002**: Navegação entre 100% das 8 telas da GUI sem falhas ou erros registrados no console da webview.
- **SC-003**: 0 janelas de console visíveis quando a GUI é aberta por duplo clique.
- **SC-004**: O executável empacotado pelo PyInstaller deve ser gerado e executado com sucesso no Windows 10 e Windows 11.

## Assumptions

- **A-001**: Presumimos que o WebView2 já está instalado no Windows 10/11 por padrão, mas trataremos a ausência de forma segura.
- **A-002**: Presumimos que não serão implementadas novas regras de otimização/limpeza ou pontos de restauração nesta fase de validação da infraestrutura GUI.
- **A-003**: Presumimos que a estrutura e estilo da GUI (HTML/CSS/JS) existente em `gui/` serão mantidos, apenas corrigindo incompatibilidades de plataforma caso encontradas.
