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

    function formatarSegundos(s) {
        if (!s) return "0s";
        var m = Math.floor(s / 60);
        var sec = s % 60;
        return m > 0 ? m + "m " + sec + "s" : sec + "s";
    }

    function formatarProtecao(status) {
        if (status === "restore_created") return "Ponto de restauração verificado";
        if (status === "risk_accepted") return "Risco aceito (sem restauração)";
        return "Não tentado";
    }

    page.showResult = function (resultado) {
        var container = document.getElementById("conteudo-relatorio");
        if (!container) return;

        if (!resultado || !resultado.antes || !resultado.depois) {
            container.innerHTML = '<div class="card"><span class="badge erro">Erro</span> Falha ao processar relatório (dados ausentes)</div>';
            return;
        }

        var antes = resultado.antes;
        var depois = resultado.depois;
        var limpeza = resultado.limpeza || {};
        var otim = resultado.otimizacao || {};
        var protecao = resultado.protecao || {};

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

        var html = '<div class="grade-cards" style="margin-bottom: 20px;">' +
            '<div class="card-metrica">' +
            '<div class="rotulo">Duração</div>' +
            '<div class="valor">' + formatarSegundos(resultado.duracao_segundos) + "</div>" +
            "</div>" +
            '<div class="card-metrica">' +
            '<div class="rotulo">Espaço Liberado</div>' +
            '<div class="valor">' + formatarBytes(limpeza.espaco_liberado_mb) + "</div>" +
            "</div>" +
            '<div class="card-metrica">' +
            '<div class="rotulo">Otimizações</div>' +
            '<div class="valor">' + (otim.sucessos || 0) + "/" + (otim.total || 0) + "</div>" +
            "</div>" +
            '<div class="card-metrica">' +
            '<div class="rotulo">Proteção</div>' +
            '<div class="valor" style="font-size: 14px; margin-top: 8px;">' + formatarProtecao(protecao.status) + "</div>" +
            "</div>" +
            "</div>";

        // Detalhes da Limpeza
        html += '<div class="card">' +
            "<strong>Detalhes da Limpeza</strong>" +
            '<table class="tabela-dados" style="margin-top:12px">' +
            "<thead><tr><th>Categoria</th><th>Arquivos</th><th>Espaço</th><th>Status</th></tr></thead>" +
            "<tbody>";

        var categorias = limpeza.categorias || [];
        if (categorias.length === 0) {
            html += '<tr><td colspan="4" class="texto-secundario">Nenhuma categoria processada.</td></tr>';
        } else {
            categorias.forEach(function(cat) {
                var arquivos = (cat.arquivos_removidos || 0) + (cat.arquivos_ignorados || 0);
                var mb = (cat.espaco_liberado_bytes || 0) / (1024*1024);
                html += '<tr>' +
                    '<td>' + (cat.nome || "Desconhecido") + '</td>' +
                    '<td>' + arquivos + '</td>' +
                    '<td>' + formatarBytes(mb) + '</td>' +
                    '<td><span class="badge ' + (cat.status === "concluido" ? "sucesso" : (cat.status === "falhou" ? "erro" : "aviso")) + '">' + (cat.status || "desconhecido").toUpperCase() + '</span></td>' +
                    '</tr>';
            });
        }
        html += "</tbody></table></div>";

        // Otimizações Aplicadas
        html += '<div class="card">' +
            "<strong>Otimizações Aplicadas</strong>" +
            '<table class="tabela-dados" style="margin-top:12px">' +
            "<thead><tr><th>Ação</th><th>Status</th></tr></thead>" +
            "<tbody>";

        var resultados_otim = otim.resultados || {};
        var chaves_otim = Object.keys(resultados_otim);
        if (chaves_otim.length === 0) {
            html += '<tr><td colspan="2" class="texto-secundario">Nenhuma otimização aplicada.</td></tr>';
        } else {
            chaves_otim.forEach(function(k) {
                var r = resultados_otim[k];
                var status = r.ok ? "OK" : "FALHOU";
                var cor = r.ok ? "sucesso" : "erro";
                html += '<tr>' +
                    '<td>' + k + '</td>' +
                    '<td><span class="badge ' + cor + '">' + status + '</span></td>' +
                    '</tr>';
            });
        }
        html += "</tbody></table></div>";

        // Estado do Sistema
        html += '<div class="card">' +
            "<strong>Estado do Sistema (Antes vs Depois)</strong>" +
            '<p class="texto-secundario" style="margin: 8px 0;">Nota: Uso de CPU/RAM são métricas oscilantes e não refletem necessariamente o ganho de FPS.</p>' +
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
            );

        var discosAntes = {};
        if (antes.discos) antes.discos.forEach(function(d) { discosAntes[d.unidade] = d.livre_gb; });
        var discosDepois = {};
        if (depois.discos) depois.discos.forEach(function(d) { discosDepois[d.unidade] = d.livre_gb; });

        Object.keys(discosAntes).forEach(function(unidade) {
            if (discosDepois[unidade] !== undefined) {
                html += linhaComparativa("Livre " + unidade, discosAntes[unidade], discosDepois[unidade], " GB", false);
            }
        });

        html += "</tbody></table></div>";

        // Exportações
        html += '<div class="card">' +
            '<strong>Relatórios Exportados</strong>' +
            '<p class="texto-secundario" style="margin-top:8px"><strong>TXT:</strong> ' + (resultado.relatorio_txt || "Indisponível") + '</p>' +
            '<p class="texto-secundario" style="margin-top:4px"><strong>HTML:</strong> ' + (resultado.relatorio_html || "Indisponível") + '</p>' +
            "</div>";

        container.innerHTML = html;
    };

})(window.Phoenix);
