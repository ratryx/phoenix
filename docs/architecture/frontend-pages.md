# Frontend Pages

O sistema de rotas carrega dinamicamente conteúdos modulares delegando a renderização para funções especializadas baseadas no namespace `Phoenix.pages.*`. Todas as páginas agora estão extraídas em `gui/js/pages/`.

## Características das Páginas Modulares
- **Isolamento de Lifecycle**: As páginas que dependem de polling assíncrono (Hardware, Sensores, Histórico) utilizam os listeners do `Phoenix.lifecycle`, assegurando a desmontagem correta ao navegar para outra página.
- **Renderização Sob Demanda**: Algumas páginas constroem seu HTML via JavaScript puro e populam listas no momento em que a página se torna ativa (ex. Sensores e Otimização).
- **Sem ES Modules**: Utilização rígida do padrão IIFE `(function(Phoenix) { ... })(window.Phoenix)`.
- **Acesso restrito ao DOM**: Cada módulo altera estritamente seu container base `<div id="pagina-X">`.
- **Prevenção de Duplicidade / Concorrência**: Requisições de carregamento que demoram (ex: Serviços ou Hardware) verificam variáveis `carregando` locais dentro da IIFE da página para prevenir cliques duplos que travariam o backend ou criariam corrida de dados.

## Páginas Específicas
* `inicio.js`: Controla macros, banners principais e tempo-real resumido.
* `diagnostico.js`: Lê o ambiente de forma controlada e exibe dados analíticos.
* `hardware.js`: Consulta profunda e manipulação da cache de métricas de Hardware.
* `sensores.js`: Polling leve e constante (`hwmonitor`), atualizando barras e displays com uso da formatação visual padrão.
* `limpeza.js`: Operações destrutivas com confirmação por modal nativo recriado.
* `otimizacao.js`: Operações destrutivas protegidas por `restore-point.js`.
* `servicos.js`: Alterações locais em serviços do Windows com feedback granular em tempo real.
* `historico.js`: Carrega a tabela cacheada do banco de dados relacional.
* `relatorio.js`: Exibição de relatórios sintéticos em memória efêmera após rotinas executadas com sucesso. Apenas uma representação visual final.
