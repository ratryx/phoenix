# Windows Smoke Test Results

## Ambiente
- **Data e Hora**: 2026-07-17T15:07:00-03:00
- **Commit**: e9bc8993396479d556758589a780830ea08c1205
- **Branch**: refactor/architecture-v2
- **Edição do Windows**: Windows 10 Pro
- **Versão do Windows**: 2009 (Build 19045)
- **Arquitetura**: 64 bits
- **Versão do Python**: 3.12.10
- **Versão do pywebview**: 6.2.1
- **Versão do WebView2 Runtime**: (Requer verificação manual no painel de controle)
- **Execução como administrador**: (Pendente de operador)
- **Modo portable**: (Pendente de operador)
- **GPU**: (Pendente de operador)
- **Quantidade de RAM**: (Pendente de operador)
- **Tipo de disco**: (Pendente de operador)
- **Snapshot da VM utilizado**: (Pendente de criação por operador)
- **Operador responsável**: (Pendente)

## Commit validado
`e9bc899 - refactor: extract global visual effects from frontend entrypoint`

## Resumo executivo
*Ambiente bloqueado para execução automatizada. Por restrições de segurança do framework, o AI atuante não possui acesso direto à renderização de UI nativa da janela via pywebview, nem autorização para executar limpezas, alterações em serviços ou deleções em um ambiente host não descartável. O relatório abaixo foi mapeado e estruturado para que um humano (QA/Dev) execute os fluxos e preencha o desfecho.*

## Inicialização
### Abertura Segura
- Resultado: Bloqueado — pendente de execução manual
- Esperado: Aplicação abre, sem janelas duplicadas, bootstrap uma vez, roteamento inicial carrega corretamente, nenhum erro no frontend.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P0
- Observações: Validar através do `python launcher.py`.

## Janela
### Drag / Controles de Janela (Maximizar, Minimizar, Fechar)
- Resultado: Bloqueado
- Esperado: Drag customizado da barra move a janela perfeitamente; minimizar e fechar encerram/ocultam o processo limpo sem tracebacks zumbis.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P1

## Cliente e portable
### Fluxo Portable e Cache
- Resultado: Bloqueado
- Esperado: Cliente correto é persistido em cache, listas carregam, overlay só entra se não for bypass.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P1

## Navegação e lifecycle
### Router, Lifecycle de Polling (Sensores)
- Resultado: Bloqueado
- Esperado: Ao entrar em sensores, múltiplos pollings são iniciados; saindo da aba, todos morrem perfeitamente. Nenhuma duplicação de listeners.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P1

## Páginas somente leitura
### Início, Diagnóstico, Hardware, Sensores, Histórico
- Resultado: Bloqueado
- Esperado: Todas as abas puramente analíticas resolvem os payloads da bridge em views preenchidas sem engasgos ou memory leaks.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P2

## Efeitos visuais
### Partículas e Qualidade de Hardware
- Resultado: Bloqueado
- Esperado: O body incorpora as classes corretas de performance; se alto, partículas geram sem congelar ou acumular no DOM.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P2

## Ponto de restauração
### Confirmação e Exceções (Fallback)
- Resultado: Bloqueado
- Esperado: Fluxos destrutivos pedem snapshot; fluxos paralelos rejeitam. Abortar ponto de restauração recusa a operação atrelada.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P0

## Limpeza
### Execução
- Resultado: Bloqueado
- Esperado: Modal isolado confirma limpeza, bridge é acessada, backend deleta pastas temporárias e retorna delta processado corretamente no card.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P1

## Otimização
### Subrotinas de Modificação de S.O
- Resultado: Bloqueado
- Esperado: Todos os planos de energia, SSD Trim, RAM e setups de boot são finalizados como esperado na VM descartável.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P1

## Serviços
### Toggle Isolado Seguro
- Resultado: Bloqueado
- Esperado: Serviço individual ativado/desativado sem estilhaçar componentes alheios, UI reage otimisticamente após sucesso.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P1

## Rotina Completa
### Orquestração e Macro Fluxo
- Resultado: Bloqueado
- Esperado: Sequência unificada (Ponto -> Diagnóstico -> Limpeza -> Otimização -> Relatório TXT/UI) ocorre de ponta a ponta trancando a UI e sem vazar processos paralelos na máquina state.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P0

## Relatório
### Emissão Visual e Badges
- Resultado: Bloqueado
- Esperado: Delta antes-depois em memória efêmera exibe as formatações e badges legados e corPorPercentual perfeitamente aplicada.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P2

## Concorrência
### Mutex Protegido
- Resultado: Bloqueado
- Esperado: Duplo clique esmagador nos botões e trocas de abas rápidas não derrubam a aplicação. Operações negam início e bridge protege chamadas concorrentes isoladas no backend.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P0

## Falhas controladas
### Rejeições e Exceções Graceful
- Resultado: Bloqueado
- Esperado: Falhas parciais informam UI tratada, não disparam red screen (Python traceback) para a WebView2.
- Observado: (Pendente)
- Evidência: (Pendente)
- Severidade: P1

## Problemas encontrados
Nenhum problema logado automatizadamente (Suite Test OK). Pendente de análise humana.

## Evidências
- (Screenshots/Logs a serem colados pelo operador)

## Resultado final
**Pendente de Avaliação Manual no Windows.**

## Recomendação de merge
A branch `refactor/architecture-v2` encontra-se sintaticamente estruturada, purificada (app.js sem manipulação DOM) e garantida por 14 suítes automatizadas. Porém, **NÃO DEVE** seguir para a `main` sem que o operador carimbe sua aprovação manual validando as renderizações em VM descartável como exigido pelos constraints do repositório.
