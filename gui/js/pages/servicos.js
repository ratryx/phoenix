/* ============================================================
   Phoenix Optimizer — Serviços (v2)
   ============================================================ */

(function (Phoenix) {
    "use strict";

    const page = {};

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.servicos = page;

    const servicosEmAlteracao = new Set();

    page.load = async function () {
        var btnServicos = document.getElementById("btn-atualizar-servicos");
        if (btnServicos && !btnServicos.dataset.eventosRegistrados) {
            btnServicos.addEventListener("click", page.load);
            btnServicos.dataset.eventosRegistrados = "true";
        }

        var container = document.getElementById("conteudo-servicos");
        if (!container) return;

        container.innerHTML = '<p class="texto-secundario">Carregando serviços...</p>';
        Phoenix.ui.feedback.mostrarOverlay("Consultando serviços do Windows...");

        try {
            var jobRes = await Phoenix.bridge.call("listar_servicos");
            if (!jobRes || !jobRes.job_id) {
                return;
            }
            var resultado = await Phoenix.jobs.awaitJob(jobRes.job_id);

            if (!resultado || !resultado.ok) {
                container.innerHTML = "";
                var errCard = document.createElement("div");
                errCard.className = "card";
                var errBadge = document.createElement("span");
                errBadge.className = "badge erro";
                errBadge.textContent = "Erro";
                errCard.appendChild(errBadge);
                errCard.appendChild(document.createTextNode(" " + ((resultado && resultado.erro) || "Erro desconhecido")));
                container.appendChild(errCard);
                return;
            }

            container.innerHTML = "";
            var card = document.createElement("div");
            card.className = "card";
            var table = document.createElement("table");
            table.className = "tabela-dados";
            var thead = document.createElement("thead");
            var trHead = document.createElement("tr");
            ["Serviço", "Status", "Ação"].forEach(function(t) {
                var th = document.createElement("th");
                th.textContent = t;
                trHead.appendChild(th);
            });
            thead.appendChild(trHead);
            table.appendChild(thead);

            var tbody = document.createElement("tbody");
            (resultado.servicos || []).forEach(function (s) {
                var ativo = s.status === "Rodando";
                var tr = document.createElement("tr");

                var tdInfo = document.createElement("td");
                var strong = document.createElement("strong");
                strong.textContent = s.nome_amigavel;
                var divDesc = document.createElement("div");
                divDesc.className = "texto-terciario";
                divDesc.textContent = s.descricao;
                tdInfo.appendChild(strong);
                tdInfo.appendChild(divDesc);
                tr.appendChild(tdInfo);

                var tdStatus = document.createElement("td");
                var spanStatus = document.createElement("span");
                spanStatus.className = "badge " + (ativo ? "sucesso" : "neutro");
                spanStatus.textContent = s.status;
                tdStatus.appendChild(spanStatus);
                tr.appendChild(tdStatus);

                var tdAcao = document.createElement("td");
                var divToggle = document.createElement("div");
                divToggle.className = "toggle " + (ativo ? "ativo" : "");
                divToggle.dataset.servico = s.nome_servico;
                divToggle.dataset.ativo = ativo.toString();
                divToggle.dataset.gerenciado = (s.managed_by_phoenix === true) ? "true" : "false";
                var divBola = document.createElement("div");
                divBola.className = "bola";
                divToggle.appendChild(divBola);
                tdAcao.appendChild(divToggle);
                tr.appendChild(tdAcao);

                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            card.appendChild(table);
            container.appendChild(card);

            // Registrar toggles dos serviços
            container.querySelectorAll(".toggle").forEach(function (toggle) {
                toggle.addEventListener("click", function () {
                    var nomeServico = toggle.dataset.servico;

                    if (servicosEmAlteracao.has(nomeServico)) return;

                    var estaAtivo = toggle.dataset.ativo === "true";

                    Phoenix.operations.restorePoint.runProtected(async function () {
                        if (servicosEmAlteracao.has(nomeServico)) return;
                        servicosEmAlteracao.add(nomeServico);

                        Phoenix.ui.feedback.mostrarOverlay(
                            estaAtivo ? "Desativando serviço..." : "Ativando serviço..."
                        );
                        try {
                            var gerenciado = toggle.dataset.gerenciado === "true";
                            var metodoAcao;
                            if (estaAtivo) {
                                metodoAcao = "desativar_servico";
                            } else {
                                metodoAcao = gerenciado ? "restaurar_servico" : "iniciar_servico";
                            }

                            var mutRes = await Phoenix.bridge.call(metodoAcao, nomeServico);
                            if (!mutRes || !mutRes.job_id) {
                                return;
                            }
                            var mutResultado = await Phoenix.jobs.awaitJob(mutRes.job_id);

                            if (mutResultado && mutResultado.ok) {
                                toggle.classList.toggle("ativo");
                                toggle.dataset.ativo = (!estaAtivo).toString();
                                if (estaAtivo) {
                                    toggle.dataset.gerenciado = "true";
                                } else if (gerenciado) {
                                    toggle.dataset.gerenciado = "false";
                                }
                            }
                        } catch (e) {
                            console.error("[ERRO] Toggle serviço:", e);
                        } finally {
                            Phoenix.ui.feedback.esconderOverlay();
                            servicosEmAlteracao.delete(nomeServico);
                        }
                    });
                });
            });
        } catch (err) {
            console.error("[ERRO] Serviços:", err);
            container.innerHTML = '<p class="texto-secundario">Erro ao carregar serviços.</p>';
        } finally {
            Phoenix.ui.feedback.esconderOverlay();
        }
    };

})(window.Phoenix);
