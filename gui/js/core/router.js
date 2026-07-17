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

        // Aciona o carregador da página se registrado
        if (_pageLoader) {
            _pageLoader(idPagina);
        }
    };

    // Compatibilidade temporária
    window.irParaPagina = Phoenix.router.navigate;

})(window.Phoenix);
