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

        container.innerHTML = '';
        const div = document.createElement("div");
        div.className = "card";

        if (!resultado || !resultado.ok) {
            const span = document.createElement("span");
            span.className = "badge erro";
            span.textContent = "Erro";
            div.appendChild(span);
            div.appendChild(document.createTextNode(" "));
            
            const txt = (resultado && resultado.erro) || "Erro desconhecido";
            div.appendChild(document.createTextNode(txt));
        } else {
            const span = document.createElement("span");
            span.className = "badge sucesso";
            span.textContent = "Concluído";
            div.appendChild(span);

            const p = document.createElement("p");
            p.style.marginTop = "10px";
            p.appendChild(document.createTextNode("Espaço total liberado: "));
            
            const strong = document.createElement("strong");
            strong.textContent = formatarBytes(resultado.espaco_liberado_mb);
            p.appendChild(strong);
            
            div.appendChild(p);
        }
        
        container.appendChild(div);
    }

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.limpeza = page;

})(window.Phoenix);
