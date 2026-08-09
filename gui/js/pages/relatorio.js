/* ============================================================
   Phoenix Optimizer — Relatório (v3)
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

    function formatarProtecao(status, msg) {
        if (status === "restore_created") return "Ponto de restauração verificado";
        if (status === "risk_accepted") return "Risco aceito (sem restauração)";
        return msg || "Não tentado";
    }

    function createEl(tag, className, text) {
        var el = document.createElement(tag);
        if (className) el.className = className;
        if (text !== undefined && text !== null) el.textContent = text;
        return el;
    }
    
    function formatarStatusLimpeza(status, ignorados) {
        var s = String(status).toLowerCase();
        if (s === "parcial" || ignorados > 0) return "CONCLUÍDO COM EXCEÇÕES";
        if (s === "concluido" || s === "concluído") return "CONCLUÍDO";
        if (s === "erro" || s === "falhou") return "FALHOU";
        if (s === "unsupported" || s === "não aplicável" || s === "nao aplicavel") return "NÃO APLICÁVEL";
        return s.toUpperCase();
    }
    
    function statusLimpezaClass(status) {
        var s = String(status).toLowerCase();
        if (s.includes("exceções") || s.includes("excecoes")) return "aviso";
        if (s === "concluído" || s === "concluido") return "sucesso";
        if (s === "falhou") return "erro";
        return "neutro";
    }

    page.showResult = function (resultado) {
        var container = document.getElementById("conteudo-relatorio");
        if (!container) return;

        container.innerHTML = "";

        if (!resultado) {
            var errDiv = createEl("div", "card");
            var badge = createEl("span", "badge erro", "Erro");
            errDiv.appendChild(badge);
            errDiv.appendChild(document.createTextNode(" Falha ao carregar relatório."));
            container.appendChild(errDiv);
            return;
        }

        var payload = resultado.payload || resultado;
        var antes = payload.antes || {};
        var depois = payload.depois || {};
        var resumo = payload.resumo || {};
        var limpeza = payload.limpeza || {};
        var otim = payload.otimizacoes || {};
        var protecao = payload.protecao || {};
        var analises = payload.analises || {};
        var recs = payload.recomendacoes || [];
        var cond = payload.acoes_condicionais || {};

        function addLinhaComparativa(tbody, rotulo, valorAntes, valorDepois, sufixo) {
            var tr = document.createElement("tr");
            tr.appendChild(createEl("td", "", rotulo));
            tr.appendChild(createEl("td", "", valorAntes + sufixo));
            tr.appendChild(createEl("td", "", valorDepois + sufixo));
            tbody.appendChild(tr);
        }

        // Grade Cards
        var gradeCards = createEl("div", "grade-cards");
        gradeCards.style.marginBottom = "20px";

        var metricas = [
            { r: "Espaço Recuperado", v: formatarBytes(resumo.espaco_liberado_mb) },
            { r: "Itens Removidos", v: String(resumo.itens_removidos || 0) },
            { r: "Otimizações", v: (resumo.otimizacoes_aplicadas || 0) + " / " + (resumo.otimizacoes_total || 0) },
            { r: "Proteção", v: formatarProtecao(protecao.status, protecao.mensagem), style: "font-size: 14px; margin-top: 8px;" }
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
        
        // Recomendações
        if (recs.length > 0) {
            var cardRecs = createEl("div", "card");
            var strRecs = document.createElement("strong");
            strRecs.textContent = "Recomendações e Achados";
            cardRecs.appendChild(strRecs);
            
            var ulRecs = createEl("ul", "lista-simples");
            ulRecs.style.marginTop = "12px";
            recs.forEach(function(r) {
                var li = document.createElement("li");
                li.style.marginBottom = "8px";
                var cor = r.nivel === "sucesso" ? "#10b981" : (r.nivel === "aviso" ? "#f59e0b" : (r.nivel === "erro" ? "#ef4444" : "#3b82f6"));
                li.style.borderLeft = "4px solid " + cor;
                li.style.paddingLeft = "8px";
                
                var title = createEl("div", "", "");
                var b = document.createElement("strong");
                b.textContent = r.titulo;
                title.appendChild(b);
                li.appendChild(title);
                
                var desc = createEl("div", "texto-secundario", r.descricao);
                li.appendChild(desc);
                
                ulRecs.appendChild(li);
            });
            cardRecs.appendChild(ulRecs);
            container.appendChild(cardRecs);
        }

        // Análises (SMART e Drivers)
        var hasSmart = analises.smart && analises.smart.ok;
        var hasDrivers = analises.drivers && analises.drivers.ok;
        
        if (hasSmart || hasDrivers) {
            var cardAnalises = createEl("div", "card");
            var strAnalises = document.createElement("strong");
            strAnalises.textContent = "Saúde do Sistema";
            cardAnalises.appendChild(strAnalises);
            
            var flex = createEl("div", "");
            flex.style.display = "flex";
            flex.style.gap = "20px";
            flex.style.marginTop = "12px";
            
            if (hasSmart) {
                var divSmart = createEl("div", "");
                divSmart.style.flex = "1";
                divSmart.appendChild(createEl("strong", "texto-secundario", "Discos (SMART)"));
                var ulSmart = createEl("ul", "lista-simples");
                var discos = analises.smart.discos || [];
                discos.forEach(function(d) {
                    var text = "Disco " + d.device_id + " (" + d.tipo_midia + "): " + d.classificacao;
                    var li = createEl("li", "", text);
                    ulSmart.appendChild(li);
                });
                divSmart.appendChild(ulSmart);
                flex.appendChild(divSmart);
            }
            
            if (hasDrivers) {
                var divDrivers = createEl("div", "");
                divDrivers.style.flex = "1";
                divDrivers.appendChild(createEl("strong", "texto-secundario", "Drivers"));
                var ulDrivers = createEl("ul", "lista-simples");
                var resultDrivers = analises.drivers.resultados || [];
                if (resultDrivers.length === 0) {
                     ulDrivers.appendChild(createEl("li", "", "OK"));
                } else {
                     resultDrivers.forEach(function(d) {
                         var text = d.nome + ": " + d.classificacao;
                         var li = createEl("li", "", text);
                         ulDrivers.appendChild(li);
                     });
                }
                divDrivers.appendChild(ulDrivers);
                flex.appendChild(divDrivers);
            }
            
            cardAnalises.appendChild(flex);
            container.appendChild(cardAnalises);
        }

        // Detalhes da Limpeza
        var cardLimpeza = createEl("div", "card");
        var strLimpeza = document.createElement("strong");
        strLimpeza.textContent = "Detalhes da Limpeza";
        cardLimpeza.appendChild(strLimpeza);

        var tabLimpeza = createEl("table", "tabela-dados");
        tabLimpeza.style.marginTop = "12px";
        var tHeadLimpeza = document.createElement("thead");
        tHeadLimpeza.innerHTML = "<tr><th>Categoria</th><th>Removidos</th><th>Preservados</th><th>Recuperado</th><th>Status</th></tr>";
        tabLimpeza.appendChild(tHeadLimpeza);

        var tBodyLimpeza = document.createElement("tbody");
        var categorias = limpeza.categorias || [];
        if (categorias.length === 0) {
            var trVazioL = document.createElement("tr");
            var tdVazioL = createEl("td", "texto-secundario", "Nenhuma categoria processada.");
            tdVazioL.colSpan = 5;
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
                var stFormatado = formatarStatusLimpeza(cat.status || "desconhecido", ignorados);
                var badgeClass = statusLimpezaClass(stFormatado);
                tdStatus.appendChild(createEl("span", "badge " + badgeClass, stFormatado));
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
                var status = r.ok ? "APLICADO" : "FALHOU";
                var cor = r.ok ? "sucesso" : "erro";
                var nome = r.descricao || k;

                var tr = document.createElement("tr");
                tr.appendChild(createEl("td", "", nome));
                var tdStatus = document.createElement("td");
                tdStatus.appendChild(createEl("span", "badge " + cor, status));
                tr.appendChild(tdStatus);
                tBodyOtim.appendChild(tr);
            });
            
            // Condicionais
            if (cond && cond.otimizacao_disco && cond.otimizacao_disco.executado) {
                var tr = document.createElement("tr");
                tr.appendChild(createEl("td", "", "Otimização de Armazenamento (" + cond.otimizacao_disco.saida + ")"));
                var tdStatus = document.createElement("td");
                tdStatus.appendChild(createEl("span", "badge sucesso", "APLICADO"));
                tr.appendChild(tdStatus);
                tBodyOtim.appendChild(tr);
            }
        }
        tabOtim.appendChild(tBodyOtim);
        cardOtim.appendChild(tabOtim);
        container.appendChild(cardOtim);

        // Estado do Sistema
        if (antes.cpu && depois.cpu) {
            var cardEstado = createEl("div", "card");
            var strEstado = document.createElement("strong");
            strEstado.textContent = "Estado do Sistema (Antes vs Depois)";
            cardEstado.appendChild(strEstado);
    
            var pNota = createEl("p", "texto-secundario", "Nota: Uso de CPU/RAM são métricas oscilantes e não refletem necessariamente o ganho de desempenho em jogos.");
            pNota.style.margin = "8px 0";
            cardEstado.appendChild(pNota);
    
            var tabEstado = createEl("table", "tabela-dados");
            var tHeadEstado = document.createElement("thead");
            tHeadEstado.innerHTML = "<tr><th>Métrica</th><th>Antes</th><th>Depois</th></tr>";
            tabEstado.appendChild(tHeadEstado);
    
            var tBodyEstado = document.createElement("tbody");
    
            addLinhaComparativa(tBodyEstado, "Uso de CPU", antes.cpu.uso_percentual, depois.cpu.uso_percentual, "%");
            addLinhaComparativa(tBodyEstado, "Uso de RAM", antes.memoria.percentual_uso, depois.memoria.percentual_uso, "%");
            addLinhaComparativa(tBodyEstado, "RAM Disponível", antes.memoria.disponivel_gb, depois.memoria.disponivel_gb, " GB");
    
            // Discos
            if (antes.discos && depois.discos) {
                var dAntes = {};
                antes.discos.forEach(function(d) { dAntes[d.unidade] = d.livre_gb; });
                var dDepois = {};
                depois.discos.forEach(function(d) { dDepois[d.unidade] = d.livre_gb; });
    
                Object.keys(dAntes).forEach(function(u) {
                    if (dDepois[u] !== undefined) {
                        addLinhaComparativa(tBodyEstado, "Armazenamento Livre (" + u + ")", dAntes[u], dDepois[u], " GB");
                    }
                });
            }
    
            tabEstado.appendChild(tBodyEstado);
            cardEstado.appendChild(tabEstado);
            container.appendChild(cardEstado);
        }
    };

})(window.Phoenix = window.Phoenix || {});
