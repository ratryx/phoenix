/* ============================================================
   Phoenix Optimizer — Histórico (v2)
   ============================================================ */

(function (Phoenix) {
    "use strict";

    const page = {};

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.historico = page;

    page.load = async function () {
        var container = document.getElementById("conteudo-historico");
        if (!container) return;

        container.innerHTML =
            '<p class="texto-secundario">Carregando histórico...</p>';
        Phoenix.ui.feedback.mostrarOverlay("Consultando histórico...");

        try {
            var resultado = await Phoenix.bridge.call("obter_historico");
            Phoenix.ui.feedback.esconderOverlay();

            if (!resultado) { 
                return; 
            }

            if (!resultado.ok) {
                container.innerHTML =
                    '<div class="card"><span class="badge erro">Erro</span> ' +
                    ((resultado && resultado.erro) || "Erro desconhecido") +
                    "</div>";
                return;
            }

            if (!resultado.atendimentos || resultado.atendimentos.length === 0) {
                container.innerHTML =
                    '<p class="texto-secundario">Nenhum atendimento registrado ainda.</p>';
                return;
            }

            var linhas = resultado.atendimentos
                .map(function (a) {
                    return (
                        "<tr>" +
                        "<td>" + a.id_atendimento + "</td>" +
                        "<td>" + a.cliente + "</td>" +
                        "<td>" + a.data_hora + "</td>" +
                        "</tr>"
                    );
                })
                .join("");

            container.innerHTML =
                '<div class="card">' +
                '<table class="tabela-dados">' +
                "<thead><tr><th>ID</th><th>Cliente</th><th>Data/Hora</th></tr></thead>" +
                "<tbody>" + linhas + "</tbody>" +
                "</table>" +
                "</div>";
        } catch (err) {
            console.error("[ERRO] Histórico:", err);
            Phoenix.ui.feedback.esconderOverlay();
        }
    };

})(window.Phoenix);
