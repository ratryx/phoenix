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
        let parcial = false;
        try {
            const jobRes = await Phoenix.bridge.call("executar_limpeza");
            if (!jobRes || !jobRes.job_id) {
                return;
            }
            const resultado = await Phoenix.jobs.awaitJob(jobRes.job_id, function(pct, msg, detalhes) {
                Phoenix.ui.feedback.atualizarOverlay(msg, pct, detalhes);
            });
            if (resultado && resultado.ok) {
                sucesso = true;
                if (resultado.parcial) parcial = true;
            }
            renderizarLimpeza(resultado);
        } catch (e) {
            console.error("[ERRO] Limpeza:", e);
        } finally {
            Phoenix.ui.feedback.esconderOverlay(true, sucesso, parcial);
            executando = false;
        }
    };

    function renderizarLimpeza(resultado) {
        const container = document.getElementById("conteudo-limpeza");
        if (!container) return;

        container.replaceChildren();
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
            
            if (resultado && resultado.espaco_liberado_mb !== undefined) {
                const p = document.createElement("p");
                p.style.marginTop = "10px";
                p.textContent = `Resultado parcial: ${formatarBytes(resultado.espaco_liberado_mb)} liberados antes da falha.`;
                div.appendChild(p);
            }
        } else {
            const span = document.createElement("span");
            span.className = "badge " + (resultado.parcial ? "alerta" : "sucesso");
            span.textContent = resultado.parcial ? "Concluído (Parcial)" : "Concluído";
            div.appendChild(span);

            const p = document.createElement("p");
            p.style.marginTop = "10px";
            p.appendChild(document.createTextNode("Espaço total liberado: "));
            
            const strong = document.createElement("strong");
            strong.textContent = formatarBytes(resultado.espaco_liberado_mb);
            p.appendChild(strong);
            
            div.appendChild(p);
            
            if (resultado.avisos && resultado.avisos.length > 0) {
                const pAvisos = document.createElement("p");
                pAvisos.style.marginTop = "10px";
                pAvisos.style.fontSize = "12px";
                pAvisos.style.color = "var(--cor-alerta-texto)";
                pAvisos.textContent = "Avisos: " + resultado.avisos.join("; ");
                div.appendChild(pAvisos);
            }
        }
        
        container.appendChild(div);
    }

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.limpeza = page;

})(window.Phoenix);
