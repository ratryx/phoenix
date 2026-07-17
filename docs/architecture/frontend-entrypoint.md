# Entrypoint e Composition Root (`gui/app.js`)

O `app.js` atua estritamente como *composition root* e inicializador da arquitetura modular do frontend do Phoenix Optimizer.

## Responsabilidades Principais
1. **Configuração do Router**: Associa os IDs de página aos `pageLoaders` injetados pelos módulos de páginas (`Phoenix.pages.*`).
2. **Qualidade Visual**: Obtém o `nivelQualidadeVisual` do backend, atualiza o CSS root e injeta as partículas caso necessário, salvando em `Phoenix.state.nivelQualidadeVisual`.
3. **Helpers Globais de Efeitos**: Mantém a implementação da utilidade `Phoenix.ui.corPorPercentual`.
4. **Bootstrapping**: Coordena a inicialização da aplicação:
   - Aguarda a `bridge` ficar pronta.
   - Inicializa as _features_ (sessão portable) e _ui_ (controles da janela).
   - Resolve os estados visuais.
   - Dispara requisições iniciais (hardware estático).
   - Registra os botões de macro/app (Diagnóstico superior, botão gigante da Rotina Completa).
   - Inicia o loop de tempo real.
   - Ativa o `router` inicializando a navegação (que consumirá hash ou roteará para `inicio`).

## O que NÃO pertence ao `app.js`
Nenhuma lógica de domínio, utilitários visuais (`corPorPercentual`), ou fluxo de renderização de qualquer espécie (`innerHTML`, `createElement`, manipulação de `document.body` e animação de partículas) pertence ao `app.js`. Utilitários visuais foram movidos para `gui/js/ui/feedback.js`, enquanto o controle dos efeitos de background (partículas e qualidade baseada em hardware) encontra-se isolado em `gui/js/ui/visual-effects.js`. Operações assíncronas complexas (como a Rotina Completa), o próprio controle do Router e do Lifecycle, e os controladores de estado da Window foram todos isolados para submódulos nas pastas `core/`, `operations/`, `ui/` e `features/`.
