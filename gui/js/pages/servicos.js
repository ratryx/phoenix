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
                Phoenix.ui.feedback.esconderOverlay(); 
                return; 
            }
            var resultado = await Phoenix.jobs.awaitJob(jobRes.job_id);
            Phoenix.ui.feedback.esconderOverlay();

            if (!resultado || !resultado.ok) {
                container.innerHTML =
                    '<div class="card"><span class="badge erro">Erro</span> ' +
                    ((resultado && resultado.erro) || "Erro desconhecido") +
                    "</div>";
                return;
            }

            var linhas = (resultado.servicos || [])
                .map(function (s) {
                    var ativo = s.status === "Rodando";
                    return (
                        "<tr>" +
                        "<td>" +
                        "<strong>" + s.nome_amigavel + "</strong>" +
                        '<div class="texto-terciario">' + s.descricao + "</div>" +
                        "</td>" +
                        "<td>" +
                        '<span class="badge ' + (ativo ? "sucesso" : "neutro") + '">' +
                        s.status +
                        "</span>" +
                        "</td>" +
                        "<td>" +
                        '<div class="toggle ' + (ativo ? "ativo" : "") + '"' +
                        ' data-servico="' + s.nome_servico + '"' +
                        ' data-ativo="' + ativo + '">' +
                        '<div class="bola"></div>' +
                        "</div>" +
                        "</td>" +
                        "</tr>"
                    );
                })
                .join("");

            container.innerHTML =
                '<div class="card">' +
                '<table class="tabela-dados">' +
                "<thead><tr><th>Serviço</th><th>Status</th><th>Ação</th></tr></thead>" +
                "<tbody>" + linhas + "</tbody>" +
                "</table>" +
                "</div>";

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
                            var metodoAcao = estaAtivo ? "desativar_servico" : "ativar_servico";
                            var mutRes = await Phoenix.bridge.call(metodoAcao, nomeServico);
                            if (!mutRes || !mutRes.job_id) { 
                                Phoenix.ui.feedback.esconderOverlay(); 
                                return; 
                            }
                            var mutResultado = await Phoenix.jobs.awaitJob(mutRes.job_id);
                            Phoenix.ui.feedback.esconderOverlay();

                            if (mutResultado && mutResultado.ok) {
                                toggle.classList.toggle("ativo");
                                toggle.dataset.ativo = (!estaAtivo).toString();
                            }
                        } catch (e) {
                            console.error("[ERRO] Toggle serviço:", e);
                            Phoenix.ui.feedback.esconderOverlay();
                        } finally {
                            servicosEmAlteracao.delete(nomeServico);
                        }
                    });
                });
            });
        } catch (err) {
            console.error("[ERRO] Serviços:", err);
            Phoenix.ui.feedback.esconderOverlay();
            container.innerHTML = '<p class="texto-secundario">Erro ao carregar serviços.</p>';
        }
    };

})(window.Phoenix);
