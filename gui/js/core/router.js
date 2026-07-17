(function (Phoenix) {
    "use strict";

    let _pageLoader = null;

    Phoenix.router.setPageLoader = function (callback) {
        _pageLoader = callback;
    };

    Phoenix.router.navigate = function (idPagina) {
        const STATE = Phoenix.state;
        
        // Notifica o ciclo de vida sobre a saída da página atual
        Phoenix.lifecycle.leavePage(STATE.paginaAtual);

        document
            .querySelectorAll(".pagina")
            .forEach(function (p) { p.classList.remove("ativa"); });
        document
            .querySelectorAll(".item-menu")
            .forEach(function (m) { m.classList.remove("ativo"); });

        var pagina = document.getElementById("pagina-" + idPagina);
        if (pagina) pagina.classList.add("ativa");

        var itemMenu = document.querySelector(
            '.item-menu[data-pagina="' + idPagina + '"]'
        );
        if (itemMenu) itemMenu.classList.add("ativo");

        STATE.paginaAtual = idPagina;

        // Atualiza a hash silenciosamente (sem disparar novo load se já estamos nela)
        if (window.location.hash !== "#" + idPagina) {
            window.location.hash = idPagina;
        }

        // Aciona o carregador da página se registrado
        if (_pageLoader) {
            _pageLoader(idPagina);
        }
    };

    Phoenix.router.initialize = function () {
        // Registro da Sidebar
        document.querySelectorAll(".item-menu[data-pagina]").forEach(function (item) {
            item.addEventListener("click", function () {
                var pagina = item.dataset.pagina;
                Phoenix.router.navigate(pagina);
            });
        });

        // Evento de Navegação Hash
        window.addEventListener("hashchange", function () {
            var novaPagina = window.location.hash.substring(1);
            if (novaPagina && novaPagina !== Phoenix.state.paginaAtual) {
                Phoenix.router.navigate(novaPagina);
            }
        });

        // Carga inicial
        var paginaInicial = window.location.hash.substring(1) || "inicio";
        Phoenix.router.navigate(paginaInicial);
    };

    // Compatibilidade temporária
    window.irParaPagina = Phoenix.router.navigate;

})(window.Phoenix);
