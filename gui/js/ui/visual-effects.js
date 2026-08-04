(function (Phoenix) {
    "use strict";

    const STATE = Phoenix.state;
    const bridge = Phoenix.bridge;
    const visualEffects = {};

    function aplicarNivelQualidade(nivel) {
        STATE.nivelQualidadeVisual = nivel;
        document.body.classList.remove(
            "qualidade-alta",
            "qualidade-media",
            "qualidade-baixa"
        );

        if (nivel === "alto") {
            document.body.classList.add("qualidade-alta");
            gerarParticulas();
        } else if (nivel === "medio") {
            document.body.classList.add("qualidade-media");
            limparParticulas();
        } else {
            document.body.classList.add("qualidade-baixa");
            limparParticulas();
        }
    }

    function limparParticulas() {
        var camada = document.getElementById("camada-particulas");
        if (camada) {
            while (camada.firstChild) { camada.removeChild(camada.firstChild); }
        }
    }

    function gerarParticulas() {
        var camada = document.getElementById("camada-particulas");
        if (!camada) return;
        while (camada.firstChild) { camada.removeChild(camada.firstChild); }

        var quantidade = 14;
        for (var i = 0; i < quantidade; i++) {
            var p = document.createElement("div");
            p.className = "particula";
            var tamanho = 4 + Math.random() * 10;
            p.style.width = tamanho + "px";
            p.style.height = tamanho + "px";
            p.style.left = Math.random() * 100 + "%";
            p.style.top = 60 + Math.random() * 40 + "%";
            p.style.animationDuration = 8 + Math.random() * 10 + "s";
            p.style.animationDelay = Math.random() * 10 + "s";
            camada.appendChild(p);
        }
    }

    visualEffects.initialize = async function() {
        try {
            var nivel = await bridge.call("obter_nivel_qualidade_visual");
            aplicarNivelQualidade(nivel || "medio");
        } catch (e) {
            aplicarNivelQualidade("medio");
        }
    };

    visualEffects.refresh = async function() {
        await visualEffects.initialize();
    };

    Phoenix.ui = Phoenix.ui || {};
    Phoenix.ui.visualEffects = visualEffects;
})(window.Phoenix);
