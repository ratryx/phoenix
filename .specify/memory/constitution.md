<!--
SYNC IMPACT REPORT
- Version change: None -> 1.0.0
- List of modified principles:
  - Added Principle I: Cirúrgico e Não Destrutivo
  - Added Principle II: Ponto de Restauração Obrigatório
  - Added Principle III: Controle de Serviços Fixos
  - Added Principle IV: Isolamento de Logs
  - Added Principle V: Transparência de Performance
  - Added Principle VI: Dual-Interface CLI/GUI
  - Added Principle VII: Validação de Empacotamento
- Added sections:
  - Technology Stack & Environment
  - Development & Verification Process
  - Governance
- Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ No updates required
  - .specify/templates/spec-template.md: ✅ No updates required
  - .specify/templates/tasks-template.md: ✅ No updates required
- Follow-up TODOs: None
-->

# Phoenix Optimizer Constitution

## Core Principles

### Principle I: Cirúrgico e Não Destrutivo
Qualquer alteração ou nova funcionalidade inserida no código deve ser extremamente cirúrgica, localizada e integrada com cautela máxima. Nunca quebrar o que já funciona.
* **Razão**: O software já está funcional e em produção; integridade e estabilidade do sistema são prioridades máximas.

### Principle II: Ponto de Restauração Obrigatório
Sempre gerar um ponto de restauração do sistema operacional antes de iniciar qualquer otimização no computador do cliente.
* **Razão**: Proteger o sistema operacional do usuário contra eventuais falhas durante a aplicação de otimizações de performance.

### Principle III: Controle de Serviços Fixos
A lista de serviços desativáveis é estritamente fixa e pré-aprovada. É proibido expandir ou alterar a lista sem revisão e aprovação prévia.
* **Razão**: Evitar que serviços essenciais do Windows sejam desativados acidentalmente, causando instabilidade no sistema operacional.

### Principle IV: Isolamento de Logs
Todos os logs do aplicativo devem ser armazenados exclusivamente no diretório `%PROGRAMDATA%\PhoenixOptimizer\logs`. Nunca gravar ou armazenar logs no diretório de instalação do programa.
* **Razão**: Garantir a conformidade com as permissões do Windows (evitar falhas de escrita em `Program Files`) e manter a organização do sistema de arquivos.

### Principle V: Transparência de Performance
Nunca prometer ganho de FPS fixo ou garantido em nenhum texto da interface com o usuário (CLI ou GUI).
* **Razão**: Expectativas reais e transparentes para o usuário, evitando alegações infundadas de ganhos de performance que variam por hardware.

### Principle VI: Dual-Interface CLI/GUI
A aplicação deve funcionar perfeitamente em ambos os modos: CLI (no terminal) e GUI (janela `pywebview`), compartilhando estritamente a mesma lógica de negócios (módulos).
* **Razão**: Garantir flexibilidade de uso e manutenção centralizada da lógica de negócios.

### Principle VII: Validação de Empacotamento
Qualquer alteração no empacotamento com PyInstaller ou na criação do instalador com Inno Setup exige a validação e teste real em uma máquina com Windows físico.
* **Razão**: O empacotamento pode introduzir erros silenciosos ou incompatibilidades em ambientes não nativos (como Wine/Linux).

## Technology Stack & Environment
O projeto utiliza a seguinte stack tecnológica:
* **Linguagem**: Python 3.12+
* **Interface Gráfica**: `pywebview` (renderizado via Microsoft WebView2 nativo no Windows)
* **Interface CLI**: CLI interativa construída com `rich` e `pyfiglet`
* **Mapeamento de Sistema**: `psutil` para diagnósticos de CPU, RAM, disco e processos
* **Interação com SO**: Execução de scripts PowerShell e comandos nativos via módulo `subprocess`
* **Logs**: Armazenados em formato estruturado (JSON/TXT) sob `%PROGRAMDATA%\PhoenixOptimizer\logs`
* **Distribuição**: Empacotamento em executável único com PyInstaller e instalador com Inno Setup

## Development & Verification Process
A evolução do codebase seguirá as prioridades e regras de validação abaixo:
* **Priorização do Backlog**:
  1. Ponto de restauração automático antes de otimizar.
  2. Verificação S.M.A.R.T. de saúde do disco.
  3. Detecção de driver de GPU desatualizado.
  4. Opção de reverter otimizações aplicadas.
  5. Detecção básica de processos suspeitos.
* **Validação Crítica de Interface (Windows real)**:
  Como a interface gráfica (`pywebview`) foi apenas validada visualmente sob Linux e nunca testada em uma instalação Windows de produção, é obrigatório testar e validar o correto funcionamento da GUI no Windows nativo como primeiro passo, antes da implementação de qualquer nova funcionalidade de negócio.

## Governance
* Esta Constituição rege todas as decisões técnicas e de design do Phoenix Optimizer.
* Emendas e alterações nos princípios exigem a evolução do número de versão deste documento seguindo o versionamento semântico (MAJOR para remoção/flexibilização de regras, MINOR para adição de novos princípios/seções, PATCH para esclarecimentos e correções ortográficas).
* Toda e qualquer implementação deve respeitar as diretrizes listadas neste documento e nas regras de execução contidas em `.antigravity/rules.md` e `AGENTS.md`.

**Version**: 1.0.0 | **Ratified**: 2026-06-24 | **Last Amended**: 2026-06-24
