(function (Phoenix) {
    "use strict";

    const page = {};
    let executando = false;

    page.load = function () {
        const btnLimpeza = document.getElementById("btn-executar-limpeza");
        if (btnLimpeza) {
            if (!btnLimpeza.dataset.eventosRegistrados) {
                btnLimpeza.addEventListener("click", page.execute);
                btnLimpeza.dataset.eventosRegistrados = "true";
            }
        }
    };

    function formatarBytes(mb) {
        if (mb >= 1024) return (mb / 1024).toFixed(2) + " GB";
        return mb.toFixed(1) + " MB";
    }

    page.execute = async function () {
        if (executando) return;
        executando = true;

        Phoenix.ui.feedback.mostrarOverlay("Limpando arquivos temporários...", true);
        let sucesso = false;
        try {
            const jobRes = await Phoenix.bridge.call("executar_limpeza");
            if (!jobRes || !jobRes.job_id) {
                return;
            }
            const resultado = await Phoenix.jobs.awaitJob(jobRes.job_id);
            if (resultado && resultado.ok) {
                sucesso = true;
            }
            renderizarLimpeza(resultado);
        } catch (e) {
            console.error("[ERRO] Limpeza:", e);
        } finally {
            Phoenix.ui.feedback.esconderOverlay(true, sucesso);
            executando = false;
        }
    };

    function renderizarLimpeza(resultado) {
        const container = document.getElementById("conteudo-limpeza");
        if (!container) return;

        if (!resultado || !resultado.ok) {
            container.innerHTML =
                '<div class="card"><span class="badge erro">Erro</span> ' +
                ((resultado && resultado.erro) || "Erro desconhecido") +
                "</div>";
            return;
        }

        container.innerHTML =
            '<div class="card">' +
            '<span class="badge sucesso">Concluído</span>' +
            '<p style="margin-top:10px">Espaço total liberado: <strong>' +
            formatarBytes(resultado.espaco_liberado_mb) +
            "</strong></p>" +
            "</div>";
    }

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.limpeza = page;

})(window.Phoenix);
