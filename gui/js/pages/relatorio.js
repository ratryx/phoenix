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

    function createEl(tag, className, text) {
        var el = document.createElement(tag);
        if (className) el.className = className;
        if (text !== undefined && text !== null) el.textContent = text;
        return el;
    }

    page.showResult = function (resultado) {
        var container = document.getElementById("conteudo-relatorio");
        if (!container) return;

        container.innerHTML = "";

        if (!resultado || !resultado.antes || !resultado.depois) {
            var errDiv = createEl("div", "card");
            var badge = createEl("span", "badge erro", "Erro");
            errDiv.appendChild(badge);
            errDiv.appendChild(document.createTextNode(" Falha ao processar relatório (dados ausentes)"));
            container.appendChild(errDiv);
            return;
        }

        var antes = resultado.antes;
        var depois = resultado.depois;
        var limpeza = resultado.limpeza || {};
        var otim = resultado.otimizacao || {};
        var protecao = resultado.protecao || {};

        function addLinhaComparativa(tbody, rotulo, valorAntes, valorDepois, sufixo, menorEMelhor, neutra) {
            var diferenca = valorDepois - valorAntes;
            var melhorou = menorEMelhor ? diferenca < 0 : diferenca > 0;
            var corDif = (Math.abs(diferenca) < 0.01 || neutra) ? "neutro" : (melhorou ? "sucesso" : "erro");
            var seta = Math.abs(diferenca) < 0.01 ? "=" : (diferenca < 0 ? "\u25BC" : "\u25B2");

            var tr = document.createElement("tr");
            tr.appendChild(createEl("td", "", rotulo));
            tr.appendChild(createEl("td", "", valorAntes + sufixo));
            tr.appendChild(createEl("td", "", valorDepois + sufixo));

            var tdRes = document.createElement("td");
            var spanRes = createEl("span", "badge " + corDif, seta + " " + Math.abs(diferenca).toFixed(1) + sufixo);
            tdRes.appendChild(spanRes);
            tr.appendChild(tdRes);
            tbody.appendChild(tr);
        }

        // Grade Cards
        var gradeCards = createEl("div", "grade-cards");
        gradeCards.style.marginBottom = "20px";

        var metricas = [
            { r: "Duração", v: formatarSegundos(resultado.duracao_segundos) },
            { r: "Espaço Liberado", v: formatarBytes(limpeza.espaco_liberado_mb) },
            { r: "Otimizações", v: (otim.sucessos || 0) + "/" + (otim.total || 0) },
            { r: "Proteção", v: formatarProtecao(protecao.status), style: "font-size: 14px; margin-top: 8px;" }
        ];

        metricas.forEach(function(m) {
            var card = createEl("div", "card-metrica");
            card.appendChild(createEl("div", "rotulo", m.r));
            var vEl = createEl("div", "valor", m.v);
            if (m.style) vEl.style.cssText = m.style;
            card.appendChild(vEl);
            gradeCards.appendChild(card);
        });
        container.appendChild(gradeCards);

        // Detalhes da Limpeza
        var cardLimpeza = createEl("div", "card");
        var strLimpeza = document.createElement("strong");
        strLimpeza.textContent = "Detalhes da Limpeza";
        cardLimpeza.appendChild(strLimpeza);

        var tabLimpeza = createEl("table", "tabela-dados");
        tabLimpeza.style.marginTop = "12px";
        var tHeadLimpeza = document.createElement("thead");
        tHeadLimpeza.innerHTML = "<tr><th>Categoria</th><th>Itens removidos</th><th>Itens ignorados</th><th>Espaço recuperado</th><th>Status</th></tr>";
        tabLimpeza.appendChild(tHeadLimpeza);

        var tBodyLimpeza = document.createElement("tbody");
        var categorias = limpeza.categorias || [];
        if (categorias.length === 0) {
            var trVazioL = document.createElement("tr");
            var tdVazioL = createEl("td", "texto-secundario", "Nenhuma categoria processada.");
            tdVazioL.colSpan = 4;
            trVazioL.appendChild(tdVazioL);
            tBodyLimpeza.appendChild(trVazioL);
        } else {
            categorias.forEach(function(cat) {
                var removidos = cat.arquivos_removidos || 0;
                var ignorados = cat.arquivos_ignorados || 0;
                var mb = (cat.espaco_liberado_bytes || 0) / (1024*1024);

                var tr = document.createElement("tr");
                tr.appendChild(createEl("td", "", cat.nome || "Desconhecido"));
                tr.appendChild(createEl("td", "", String(removidos)));
                tr.appendChild(createEl("td", "", String(ignorados)));
                tr.appendChild(createEl("td", "", formatarBytes(mb)));

                var tdStatus = document.createElement("td");
                var badgeClass = cat.status === "concluido" ? "sucesso" : (cat.status === "falhou" ? "erro" : "aviso");
                tdStatus.appendChild(createEl("span", "badge " + badgeClass, (cat.status || "desconhecido").toUpperCase()));
                tr.appendChild(tdStatus);
                tBodyLimpeza.appendChild(tr);
            });
        }
        tabLimpeza.appendChild(tBodyLimpeza);
        cardLimpeza.appendChild(tabLimpeza);
        container.appendChild(cardLimpeza);

        // Otimizações Aplicadas
        var cardOtim = createEl("div", "card");
        var strOtim = document.createElement("strong");
        strOtim.textContent = "Otimizações Aplicadas";
        cardOtim.appendChild(strOtim);

        var tabOtim = createEl("table", "tabela-dados");
        tabOtim.style.marginTop = "12px";
        var tHeadOtim = document.createElement("thead");
        tHeadOtim.innerHTML = "<tr><th>Ação</th><th>Status</th></tr>";
        tabOtim.appendChild(tHeadOtim);

        var tBodyOtim = document.createElement("tbody");
        var resultados_otim = otim.resultados || {};
        var chaves_otim = Object.keys(resultados_otim);

        if (chaves_otim.length === 0) {
            var trVazioO = document.createElement("tr");
            var tdVazioO = createEl("td", "texto-secundario", "Nenhuma otimização aplicada.");
            tdVazioO.colSpan = 2;
            trVazioO.appendChild(tdVazioO);
            tBodyOtim.appendChild(trVazioO);
        } else {
            chaves_otim.forEach(function(k) {
                var r = resultados_otim[k];
                var status = r.ok ? "OK" : "FALHOU";
                var cor = r.ok ? "sucesso" : "erro";
                var nome = r.descricao || k;

                var tr = document.createElement("tr");
                tr.appendChild(createEl("td", "", nome));
                var tdStatus = document.createElement("td");
                tdStatus.appendChild(createEl("span", "badge " + cor, status));
                tr.appendChild(tdStatus);
                tBodyOtim.appendChild(tr);
            });
        }
        tabOtim.appendChild(tBodyOtim);
        cardOtim.appendChild(tabOtim);
        container.appendChild(cardOtim);

        // Estado do Sistema
        var cardEstado = createEl("div", "card");
        var strEstado = document.createElement("strong");
        strEstado.textContent = "Estado do Sistema (Antes vs Depois)";
        cardEstado.appendChild(strEstado);

        var pNota = createEl("p", "texto-secundario", "Nota: Uso de CPU/RAM são métricas oscilantes e não refletem necessariamente o ganho de FPS.");
        pNota.style.margin = "8px 0";
        cardEstado.appendChild(pNota);

        var tabEstado = createEl("table", "tabela-dados");
        tabEstado.style.marginTop = "12px";
        var tHeadEstado = document.createElement("thead");
        tHeadEstado.innerHTML = "<tr><th>Métrica</th><th>Antes</th><th>Depois</th><th>Variação</th></tr>";
        tabEstado.appendChild(tHeadEstado);

        var tBodyEstado = document.createElement("tbody");

        if (antes.cpu && depois.cpu) {
            addLinhaComparativa(tBodyEstado, "Uso de CPU", antes.cpu.uso_percentual, depois.cpu.uso_percentual, "%", true, true);
        }
        if (antes.memoria && depois.memoria) {
            addLinhaComparativa(tBodyEstado, "Uso de RAM", antes.memoria.percentual_uso, depois.memoria.percentual_uso, "%", true, true);
            addLinhaComparativa(tBodyEstado, "RAM disponível", antes.memoria.disponivel_gb, depois.memoria.disponivel_gb, " GB", false, true);
        }

        var discosAntes = {};
        if (antes.discos) antes.discos.forEach(function(d) { discosAntes[d.unidade] = d.livre_gb; });
        var discosDepois = {};
        if (depois.discos) depois.discos.forEach(function(d) { discosDepois[d.unidade] = d.livre_gb; });

        Object.keys(discosAntes).forEach(function(unidade) {
            if (discosDepois[unidade] !== undefined) {
                addLinhaComparativa(tBodyEstado, "Livre " + unidade, discosAntes[unidade], discosDepois[unidade], " GB", false, false);
            }
        });

        tabEstado.appendChild(tBodyEstado);
        cardEstado.appendChild(tabEstado);
        container.appendChild(cardEstado);

        // Exportações
        var cardExp = createEl("div", "card");
        var strExp = document.createElement("strong");
        strExp.textContent = "Relatórios Exportados";
        cardExp.appendChild(strExp);

        var pTxt = createEl("p", "texto-secundario", "");
        pTxt.style.marginTop = "8px";
        var sTxt = document.createElement("strong");
        sTxt.textContent = "TXT: ";
        pTxt.appendChild(sTxt);
        pTxt.appendChild(document.createTextNode(resultado.relatorio_txt || "Indisponível"));
        cardExp.appendChild(pTxt);

        var pHtml = createEl("p", "texto-secundario", "");
        pHtml.style.marginTop = "4px";
        var sHtml = document.createElement("strong");
        sHtml.textContent = "HTML: ";
        pHtml.appendChild(sHtml);
        pHtml.appendChild(document.createTextNode(resultado.relatorio_html || "Indisponível"));
        cardExp.appendChild(pHtml);

        container.appendChild(cardExp);
    };

})(window.Phoenix);
