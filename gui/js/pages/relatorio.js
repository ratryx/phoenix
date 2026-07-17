/* ============================================================
   Phoenix Optimizer — Relatório (v2)
   ============================================================ */

(function (Phoenix) {
    "use strict";

    const page = {};

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.relatorio = page;

    function formatarBytes(mb) {
        if (mb === undefined || mb === null) return "N/D";
        if (mb >= 1024) return (mb / 1024).toFixed(2) + " GB";
        return mb.toFixed(1) + " MB";
    }

    page.load = async function () {
        // O Relatório não busca dados na inicialização.
        // O conteúdo é gerado sob demanda pela Rotina Completa.
        var container = document.getElementById("conteudo-relatorio");
        if (container && container.innerHTML.trim() === "") {
            container.innerHTML = '<p class="texto-secundario">Nenhum relatório disponível. Execute a rotina completa primeiro.</p>';
        }
    };

    page.showResult = function (resultado) {
        var container = document.getElementById("conteudo-relatorio");
        if (!container) return;

        if (!resultado || !resultado.antes || !resultado.depois) {
            container.innerHTML = '<div class="card"><span class="badge erro">Erro</span> Falha ao processar relatório (dados ausentes)</div>';
            return;
        }

        var antes = resultado.antes;
        var depois = resultado.depois;

        function linhaComparativa(rotulo, valorAntes, valorDepois, sufixo, menorEMelhor) {
            var diferenca = valorDepois - valorAntes;
            var melhorou = menorEMelhor ? diferenca < 0 : diferenca > 0;
            var corDif =
                Math.abs(diferenca) < 0.01
                    ? "neutro"
                    : melhorou
                        ? "sucesso"
                        : "erro";
            var seta =
                Math.abs(diferenca) < 0.01
                    ? "="
                    : melhorou
                        ? "\u25BC"
                        : "\u25B2";
            return (
                "<tr>" +
                "<td>" + rotulo + "</td>" +
                "<td>" + valorAntes + sufixo + "</td>" +
                "<td>" + valorDepois + sufixo + "</td>" +
                '<td><span class="badge ' + corDif + '">' +
                seta + " " + Math.abs(diferenca).toFixed(1) + sufixo +
                "</span></td>" +
                "</tr>"
            );
        }

        container.innerHTML =
            '<div class="grade-cards">' +
            '<div class="card-metrica">' +
            '<div class="rotulo">Espaço liberado</div>' +
            '<div class="valor">' + formatarBytes(resultado.espaco_liberado_mb) + "</div>" +
            "</div>" +
            "</div>" +
            '<div class="card">' +
            "<strong>CPU & memória — antes vs depois</strong>" +
            '<table class="tabela-dados" style="margin-top:12px">' +
            "<thead><tr><th>Métrica</th><th>Antes</th><th>Depois</th><th>Variação</th></tr></thead>" +
            "<tbody>" +
            linhaComparativa(
                "Uso de CPU",
                antes.cpu.uso_percentual,
                depois.cpu.uso_percentual,
                "%",
                true
            ) +
            linhaComparativa(
                "Uso de RAM",
                antes.memoria.percentual_uso,
                depois.memoria.percentual_uso,
                "%",
                true
            ) +
            linhaComparativa(
                "RAM disponível",
                antes.memoria.disponivel_gb,
                depois.memoria.disponivel_gb,
                " GB",
                false
            ) +
            "</tbody>" +
            "</table>" +
            "</div>" +
            '<div class="card">' +
            '<span class="badge sucesso">Relatório exportado</span>' +
            '<p class="texto-secundario" style="margin-top:8px">' +
            (resultado.relatorio_txt || "Caminho indisponível") +
            "</p>" +
            "</div>";
    };

})(window.Phoenix);
