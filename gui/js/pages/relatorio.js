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

        // A. Identity
        var cardId = createEl("div", "card");
        cardId.style.marginBottom = "20px";
        var titleId = createEl("h3", "", "Identificação do Atendimento");
        titleId.style.marginTop = "0";
        cardId.appendChild(titleId);

        var listId = createEl("ul", "lista-simples");
        listId.appendChild(createEl("li", "", "Cliente: " + (antes.cliente || "Não informado")));
        listId.appendChild(createEl("li", "", "Atendimento ID: " + (payload.id_atendimento || "N/D")));
        listId.appendChild(createEl("li", "", "Data/Hora: " + (depois.data_hora || "N/D")));
        if (antes.sistema) {
            listId.appendChild(createEl("li", "", "SO: " + (antes.sistema.sistema || "") + " " + (antes.sistema.versao || "")));
            listId.appendChild(createEl("li", "", "CPU: " + (antes.sistema.processador || "N/D")));
        }
        if (antes.memoria) {
            listId.appendChild(createEl("li", "", "RAM Total: " + (antes.memoria.total_gb || "N/D") + " GB"));
        }
        cardId.appendChild(listId);
        container.appendChild(cardId);

        // B. Summary Cards
        var gradeCards = createEl("div", "grade-cards");
        gradeCards.style.marginBottom = "20px";

        var isRiskAccepted = protecao.status === "risk_accepted";
        var protecaoStyle = isRiskAccepted ? "font-size: 14px; margin-top: 8px; color: #f59e0b; font-weight: bold;" : "font-size: 14px; margin-top: 8px;";

        var metricas = [
            { r: "Espaço Recuperado", v: formatarBytes(resumo.espaco_liberado_mb) },
            { r: "Itens Removidos", v: String(resumo.itens_removidos || 0) },
            { r: "Otimizações", v: (resumo.otimizacoes_aplicadas || 0) + " / " + (resumo.otimizacoes_total || 0) },
            { r: "Duração", v: formatarSegundos(payload.duracao_segundos) },
            { r: "Proteção", v: formatarProtecao(protecao.status, protecao.mensagem), style: protecaoStyle }
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

        // C1. Achados do Sistema
        var startup = analises.startup || {};
        if (startup.ok) {
            var cardAchados = createEl("div", "card");
            cardAchados.appendChild(createEl("strong", "", "Achados do Sistema"));
            var ulAchados = createEl("ul", "lista-simples");
            ulAchados.style.marginTop = "12px";
            ulAchados.appendChild(createEl("li", "", (startup.alto_impacto || 0) + " programa(s) de inicialização com potencial impacto identificado(s)."));
            cardAchados.appendChild(ulAchados);
            container.appendChild(cardAchados);
        }

        // C2. Recomendações
        if (recs.length > 0) {
            var cardRecs = createEl("div", "card");
            cardRecs.appendChild(createEl("strong", "", "Recomendações"));
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

        // D. Saúde do Sistema (SMART / Drivers Detailed)
        var hasSmart = analises.smart && analises.smart.ok;
        var hasDrivers = analises.drivers && analises.drivers.ok;

        if (hasSmart || hasDrivers) {
            var cardAnalises = createEl("div", "card");
            cardAnalises.appendChild(createEl("strong", "", "Saúde do Sistema"));

            var flex = createEl("div", "");
            flex.style.display = "flex";
            flex.style.flexDirection = "column";
            flex.style.gap = "20px";
            flex.style.marginTop = "12px";

            if (hasSmart) {
                var divSmart = createEl("div", "");
                divSmart.appendChild(createEl("strong", "texto-secundario", "Discos (SMART)"));
                var ulSmart = createEl("ul", "lista-simples");
                var discos = analises.smart.discos || [];
                discos.forEach(function(d) {
                    var li = createEl("li", "", "");
                    li.appendChild(createEl("strong", "", "Disco " + d.device_id + " (" + (d.tipo_midia || "N/D") + "): "));
                    li.appendChild(document.createTextNode(d.classificacao));

                    var subUl = createEl("ul", "lista-simples");
                    subUl.style.marginLeft = "20px";
                    subUl.style.fontSize = "0.9em";
                    if (d.nome) subUl.appendChild(createEl("li", "", "Nome/modelo: " + d.nome));
                    if (d.tipo_midia) subUl.appendChild(createEl("li", "", "Tipo: " + d.tipo_midia));
                    if (d.tamanho_gb) subUl.appendChild(createEl("li", "", "Capacidade: " + d.tamanho_gb + " GB"));

                    if (d.confiabilidade) {
                        var c = d.confiabilidade;
                        if (c.temperatura_c !== undefined && c.temperatura_c !== null) subUl.appendChild(createEl("li", "", "Temperatura: " + c.temperatura_c + "°C"));
                        if (c.horas_uso !== undefined && c.horas_uso !== null) subUl.appendChild(createEl("li", "", "Horas de uso: " + c.horas_uso));
                        if (c.wear_percent !== undefined && c.wear_percent !== null) subUl.appendChild(createEl("li", "", "Desgaste: " + c.wear_percent + "%"));
                        if (c.erros_leitura) subUl.appendChild(createEl("li", "texto-erro", "Erros de leitura: " + c.erros_leitura));
                        if (c.erros_escrita) subUl.appendChild(createEl("li", "texto-erro", "Erros de escrita: " + c.erros_escrita));
                    }
                    if (d.alertas && d.alertas.length > 0) {
                        subUl.appendChild(createEl("li", "texto-erro", "Alertas: " + d.alertas.join(", ")));
                    }
                    li.appendChild(subUl);
                    ulSmart.appendChild(li);
                });
                divSmart.appendChild(ulSmart);
                flex.appendChild(divSmart);
            }

            if (hasDrivers) {
                var divDrivers = createEl("div", "");
                divDrivers.appendChild(createEl("strong", "texto-secundario", "Drivers de Vídeo"));
                var ulDrivers = createEl("ul", "lista-simples");
                var resultDrivers = analises.drivers.resultados || [];
                if (resultDrivers.length === 0) {
                     ulDrivers.appendChild(createEl("li", "", "Nenhum driver de vídeo reportado."));
                } else {
                     resultDrivers.forEach(function(d) {
                         var li = createEl("li", "", "");
                         li.appendChild(createEl("strong", "", d.nome + " (" + (d.fabricante || "N/D") + "): "));
                         li.appendChild(document.createTextNode(d.classificacao));

                         var subUl = createEl("ul", "lista-simples");
                         subUl.style.marginLeft = "20px";
                         subUl.style.fontSize = "0.9em";
                         subUl.appendChild(createEl("li", "", "Tipo: " + (d.tipo_adaptador || "N/D")));
                         subUl.appendChild(createEl("li", "", "Versão: " + (d.versao_driver || "N/D")));
                         subUl.appendChild(createEl("li", "", "Data do driver: " + (d.data_driver || "N/D")));
                         li.appendChild(subUl);
                         ulDrivers.appendChild(li);
                     });
                }
                divDrivers.appendChild(ulDrivers);
                flex.appendChild(divDrivers);
            }

            cardAnalises.appendChild(flex);
            container.appendChild(cardAnalises);
        }

        // F. Trabalho Realizado (Otimizações)
        var cardOtim = createEl("div", "card");
        cardOtim.appendChild(createEl("strong", "", "Trabalho Realizado (Otimizações)"));

        var tabOtim = createEl("table", "tabela-dados");
        tabOtim.style.marginTop = "12px";
        var tHeadOtim = document.createElement("thead");
        tHeadOtim.innerHTML = "<tr><th>Ação</th><th>Antes</th><th>Ação do Sistema</th><th>Status</th></tr>";
        tabOtim.appendChild(tHeadOtim);

        var tBodyOtim = document.createElement("tbody");
        var resultados_otim = otim.resultados || {};
        var before_state = otim.before_state || {};
        var chaves_otim = Object.keys(resultados_otim);

        if (chaves_otim.length === 0) {
            var trVazioO = document.createElement("tr");
            var tdVazioO = createEl("td", "texto-secundario", "Nenhuma otimização aplicada.");
            tdVazioO.colSpan = 4;
            trVazioO.appendChild(tdVazioO);
            tBodyOtim.appendChild(trVazioO);
        } else {
            chaves_otim.forEach(function(k) {
                var r = resultados_otim[k];
                var status = r.ok ? "APLICADO" : "FALHOU";
                var cor = r.ok ? "sucesso" : "erro";
                var nome = r.descricao || k;

                var estadoAntes = "N/D";
                if (before_state[k]) {
                    estadoAntes = before_state[k].ativo ? "Já aplicado" : "Não aplicado";
                }

                var tr = document.createElement("tr");
                tr.appendChild(createEl("td", "", nome));
                tr.appendChild(createEl("td", "", estadoAntes));
                tr.appendChild(createEl("td", "", "Otimizar"));
                var tdStatus = document.createElement("td");
                tdStatus.appendChild(createEl("span", "badge " + cor, status));
                tr.appendChild(tdStatus);
                tBodyOtim.appendChild(tr);
            });

            if (cond && cond.otimizacao_disco && cond.otimizacao_disco.executado) {
                var tr = document.createElement("tr");
                tr.appendChild(createEl("td", "", "Otimização de Armazenamento (" + cond.otimizacao_disco.saida + ")"));
                tr.appendChild(createEl("td", "", "N/D"));
                tr.appendChild(createEl("td", "", "Otimizar"));
                var tdStatus = document.createElement("td");
                tdStatus.appendChild(createEl("span", "badge sucesso", "APLICADO"));
                tr.appendChild(tdStatus);
                tBodyOtim.appendChild(tr);
            }
        }
        tabOtim.appendChild(tBodyOtim);
        cardOtim.appendChild(tabOtim);
        container.appendChild(cardOtim);

        // E. Detalhes da Limpeza (com Totais)
        var cardLimpeza = createEl("div", "card");
        cardLimpeza.appendChild(createEl("strong", "", "Detalhes da Limpeza"));

        var tabLimpeza = createEl("table", "tabela-dados");
        tabLimpeza.style.marginTop = "12px";
        var tHeadLimpeza = document.createElement("thead");
        tHeadLimpeza.innerHTML = "<tr><th>Categoria</th><th>Removidos</th><th>Preservados</th><th>Recuperado</th><th>Status</th></tr>";
        tabLimpeza.appendChild(tHeadLimpeza);

        var tBodyLimpeza = document.createElement("tbody");
        var categorias = limpeza.categorias || [];
        var totalRemovidos = 0;
        var totalPreservados = 0;

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

                totalRemovidos += removidos;
                totalPreservados += ignorados;

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

            var trFooter = document.createElement("tr");
            trFooter.style.fontWeight = "bold";
            trFooter.appendChild(createEl("td", "", "TOTAIS"));
            trFooter.appendChild(createEl("td", "", String(totalRemovidos)));
            trFooter.appendChild(createEl("td", "", String(totalPreservados)));
            trFooter.appendChild(createEl("td", "", formatarBytes(resumo.espaco_liberado_mb)));
            trFooter.appendChild(createEl("td", "", ""));
            tBodyLimpeza.appendChild(trFooter);
        }
        tabLimpeza.appendChild(tBodyLimpeza);
        cardLimpeza.appendChild(tabLimpeza);
        container.appendChild(cardLimpeza);

        // G. Estado do Sistema (Antes vs Depois)
        if (antes.cpu && depois.cpu) {
            var cardEstado = createEl("div", "card");
            cardEstado.appendChild(createEl("strong", "", "Estado do Sistema (Antes vs Depois)"));

            var pNota = createEl("p", "texto-secundario", "Nota: CPU e RAM são medições pontuais e podem variar durante o uso. Isoladamente, essas métricas não representam ganho ou perda de desempenho.");
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

        // H. Botões de Ação
        // H. Botões de Ação
        var actionContainer = createEl("div", "");
        actionContainer.style.display = "flex";
        actionContainer.style.gap = "10px";
        actionContainer.style.marginTop = "20px";
        actionContainer.style.flexWrap = "wrap";

        if (Phoenix.bridge) {
            if (Phoenix.bridge.abrir_pasta_relatorio) {
                var btnAbrirPasta = createEl("button", "botao", "Abrir pasta do relatório");
                btnAbrirPasta.onclick = function() {
                    Phoenix.bridge.abrir_pasta_relatorio(payload.id_atendimento);
                };
                actionContainer.appendChild(btnAbrirPasta);
            }
            if (Phoenix.bridge.abrir_relatorio_html && payload.relatorio_html) {
                var btnAbrirHtml = createEl("button", "botao", "Abrir relatório HTML");
                btnAbrirHtml.onclick = function() {
                    Phoenix.bridge.abrir_relatorio_html(payload.id_atendimento);
                };
                actionContainer.appendChild(btnAbrirHtml);
            }
        }

        if (typeof window.print === "function") {
            var btnImprimir = createEl("button", "botao", "Imprimir / PDF");
            btnImprimir.onclick = function() {
                try {
                    window.print();
                } catch (e) {
                    console.error("Falha ao imprimir", e);
                }
            };
            actionContainer.appendChild(btnImprimir);
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
            var btnCopiar = createEl("button", "botao", "Copiar resumo");
            btnCopiar.onclick = function() {
                var resumoTexto = "Relatório Phoenix Optimizer - " + (antes.cliente || "Cliente") + "\n";
                resumoTexto += "Espaço liberado: " + (resumo.espaco_liberado_mb ? (resumo.espaco_liberado_mb / 1024).toFixed(2) + " GB" : "0 GB") + "\n";
                resumoTexto += "Otimizações: " + (resumo.otimizacoes_aplicadas || 0) + "/" + (resumo.otimizacoes_total || 0) + "\n";
                navigator.clipboard.writeText(resumoTexto).then(function() {
                    btnCopiar.textContent = "Copiado!";
                    setTimeout(function() { btnCopiar.textContent = "Copiar resumo"; }, 2000);
                }).catch(function(e) {
                    console.error("Falha ao copiar", e);
                });
            };
            actionContainer.appendChild(btnCopiar);
        }

        if (actionContainer.children.length > 0) {
            container.appendChild(actionContainer);
        }
    };

})(window.Phoenix = window.Phoenix || {});
