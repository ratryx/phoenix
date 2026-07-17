(function (Phoenix) {
    "use strict";

    const bridge = Phoenix.bridge;

    const ui = {};

    function registrarBotoesJanela() {
        var btnMin = document.getElementById("btn-minimizar");
        if (btnMin) {
            btnMin.addEventListener("click", function () {
                bridge.call("minimizar_janela");
            });
        }

        var btnFechar = document.getElementById("btn-fechar");
        if (btnFechar) {
            btnFechar.addEventListener("click", function () {
                bridge.call("fechar_janela");
            });
        }
    }

    function registrarDrag() {
        var estaArrastando = false;
        var ultimoX = 0;
        var ultimoY = 0;
        var animFrameId = null;

        function processarMovimento() {
            if (estaArrastando && bridge.isReady()) {
                bridge.call("mover_janela", ultimoX, ultimoY);
                animFrameId = requestAnimationFrame(processarMovimento);
            } else {
                animFrameId = null;
            }
        }

        // Elementos que iniciam drag
        var elementosDrag = [];

        var titlebar = document.querySelector(".barra-titulo");
        if (titlebar) elementosDrag.push(titlebar);

        document.querySelectorAll(".cabecalho-pagina").forEach(function (el) {
            elementosDrag.push(el);
        });

        elementosDrag.forEach(function (el) {
            el.addEventListener("mousedown", function (e) {
                // Ignorar cliques em elementos interativos
                if (
                    e.target.closest("button") ||
                    e.target.closest("input") ||
                    e.target.closest("a") ||
                    e.target.closest(".controles-janela")
                ) {
                    return;
                }

                estaArrastando = true;
                ultimoX = e.screenX;
                ultimoY = e.screenY;

                var winX = e.screenX - e.clientX;
                var winY = e.screenY - e.clientY;

                if (bridge.isReady()) {
                    bridge.call("iniciar_drag", e.screenX, e.screenY, winX, winY);
                }

                if (!animFrameId) {
                    animFrameId = requestAnimationFrame(processarMovimento);
                }
            });
        });

        // mousemove — só atualiza coordenadas, sem flood de chamadas API
        window.addEventListener("mousemove", function (e) {
            if (estaArrastando) {
                ultimoX = e.screenX;
                ultimoY = e.screenY;
            }
        });

        // mouseup — para o drag
        window.addEventListener("mouseup", function () {
            if (estaArrastando) {
                estaArrastando = false;
                if (animFrameId) {
                    cancelAnimationFrame(animFrameId);
                    animFrameId = null;
                }
                if (bridge.isReady()) {
                    bridge.call("parar_drag");
                }
            }
        });
    }

    ui.initialize = function () {
        registrarBotoesJanela();
        registrarDrag();
    };

    Phoenix.ui = Phoenix.ui || {};
    Phoenix.ui.windowControls = ui;

})(window.Phoenix);
