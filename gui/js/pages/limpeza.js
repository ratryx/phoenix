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

        Phoenix.ui.feedback.mostrarOverlay("Limpando arquivos temporários...", { destrutivo: true, cancelavel: true });

        const abortController = new AbortController();
        const btnCancelar = document.getElementById("overlay-btn-cancelar");

        if (btnCancelar) {
            btnCancelar.onclick = () => {
                btnCancelar.disabled = true;
                btnCancelar.textContent = "Cancelando...";
                abortController.abort();
            };
        }

        let sucesso = false;
        let parcial = false;
        try {
            const jobRes = await Phoenix.bridge.call("executar_limpeza");
            if (!jobRes || !jobRes.job_id) {
                executando = false;
                Phoenix.ui.feedback.esconderOverlay(true, false, false);
                return;
            }
            const resultado = await Phoenix.jobs.awaitJob(jobRes.job_id, {
                progressCallback: function(pct, msg, detalhes) {
                    Phoenix.ui.feedback.atualizarOverlay(msg, pct, detalhes);
                },
                signal: abortController.signal
            });

            if (resultado && resultado.ok) {
                sucesso = true;
                if (resultado.parcial) parcial = true;
            }
            renderizarLimpeza(resultado);
        } catch (e) {
            console.error("[ERRO] Limpeza:", e);
        } finally {
            if (btnCancelar) btnCancelar.onclick = null;
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
            span.textContent = (resultado && resultado.codigo === "JOB_CANCELLED") ? "Cancelado" : "Erro";
            div.appendChild(span);
            div.appendChild(document.createTextNode(" "));

            const txt = (resultado && resultado.erro) || "Erro desconhecido";
            div.appendChild(document.createTextNode(txt));

            // Fallback para timeout ou cancelamento (MOSTRAR RESULTADO PARCIAL)
            const snap = resultado && resultado.resultado_parcial;
            if (snap) {
                const espaco = snap.espaco_liberado_mb !== undefined ? snap.espaco_liberado_mb : (snap.espaco_liberado_bytes ? (snap.espaco_liberado_bytes / (1024*1024)) : 0);
                if (espaco > 0 || snap.arquivos_processados > 0) {
                    const p = document.createElement("p");
                    p.style.marginTop = "10px";
                    p.style.fontSize = "13px";
                    p.textContent = `Resultado parcial: ${snap.arquivos_processados} itens processados (${snap.arquivos_removidos} removidos, ${snap.arquivos_ignorados} ignorados). ${formatarBytes(espaco)} liberados antes da interrupção.`;
                    div.appendChild(p);
                }
                if (snap.categoria) {
                    const pCat = document.createElement("p");
                    pCat.style.marginTop = "4px";
                    pCat.style.fontSize = "13px";
                    pCat.textContent = `Parou na categoria: ${snap.categoria}`;
                    div.appendChild(pCat);
                }
            } else if (resultado && resultado.espaco_liberado_mb !== undefined) {
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

            const proc = (resultado.arquivos_processados !== undefined) ? resultado.arquivos_processados : (resultado.resultado_parcial && resultado.resultado_parcial.arquivos_processados !== undefined ? resultado.resultado_parcial.arquivos_processados : 0);
            const tot = (resultado.arquivos_total !== undefined) ? resultado.arquivos_total : (resultado.resultado_parcial && resultado.resultado_parcial.arquivos_total !== undefined ? resultado.resultado_parcial.arquivos_total : 0);
            const rem = (resultado.arquivos_removidos !== undefined) ? resultado.arquivos_removidos : (resultado.resultado_parcial && resultado.resultado_parcial.arquivos_removidos !== undefined ? resultado.resultado_parcial.arquivos_removidos : 0);
            const ign = (resultado.arquivos_ignorados !== undefined) ? resultado.arquivos_ignorados : (resultado.resultado_parcial && resultado.resultado_parcial.arquivos_ignorados !== undefined ? resultado.resultado_parcial.arquivos_ignorados : 0);

            const resStats = document.createElement("p");
            resStats.style.marginTop = "4px";
            resStats.style.fontSize = "13px";
            resStats.style.color = "var(--cor-texto-secundario)";
            resStats.textContent = `Processados: ${proc} / ${tot} itens (${rem} removidos, ${ign} ignorados).`;
            div.appendChild(resStats);

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
