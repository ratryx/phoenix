(function (Phoenix) {
    "use strict";

    // Preserva exatamente as mesmas chaves e valores iniciais do app.js original.
    Phoenix.state = {
        hardware: null,
        nivelQualidadeVisual: "medio",
        paginaAtual: "inicio",
        intervalos: {
            tempoReal: null,
        },
        restorePointCreatedThisSession: false,
        acaoPendenteAposRestauracao: null,
    };

})(window.Phoenix);
