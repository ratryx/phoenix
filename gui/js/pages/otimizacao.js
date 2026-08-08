(function (Phoenix) {
    "use strict";

    const page = {};
    
    let executandoGeral = false;
    let executandoGaming = false;
    let executandoDisco = false;
    let executandoRam = false;
    let executandoStartup = false;

    page.load = function () {
        const btnOtGeral = document.getElementById("btn-otimizacao-geral");
        if (btnOtGeral && !btnOtGeral.dataset.eventosRegistrados) {
            btnOtGeral.addEventListener("click", page.executeGeneral);
            btnOtGeral.dataset.eventosRegistrados = "true";
        }

        const btnOtGaming = document.getElementById("btn-otimizacao-gaming");
        if (btnOtGaming && !btnOtGaming.dataset.eventosRegistrados) {
            btnOtGaming.addEventListener("click", page.executeGaming);
            btnOtGaming.dataset.eventosRegistrados = "true";
        }

        const btnDisco = document.getElementById("btn-otimizar-disco");
        if (btnDisco && !btnDisco.dataset.eventosRegistrados) {
            btnDisco.addEventListener("click", page.optimizeDisk);
            btnDisco.dataset.eventosRegistrados = "true";
        }

        const btnRam = document.getElementById("btn-liberar-ram");
        if (btnRam && !btnRam.dataset.eventosRegistrados) {
            btnRam.addEventListener("click", page.releaseStandbyMemory);
            btnRam.dataset.eventosRegistrados = "true";
        }

        const btnStartup = document.getElementById("btn-analisar-startup");
        if (btnStartup && !btnStartup.dataset.eventosRegistrados) {
            btnStartup.addEventListener("click", page.analyzeStartup);
            btnStartup.dataset.eventosRegistrados = "true";
        }
    };

    function exibirResultadoOtimizacao(resultado, mensagemSucesso) {
        const container = document.getElementById("resultado-otimizacao");
        if (!container) return;

        while (container.firstChild) { container.removeChild(container.firstChild); }
        const div = document.createElement("div");
        div.className = "card";
        const span = document.createElement("span");
        
        if (!resultado || !resultado.ok) {
            span.className = "badge erro";
            span.textContent = "Erro";
            div.appendChild(span);
            div.appendChild(document.createTextNode(" " + ((resultado && resultado.erro) || "Erro desconhecido")));
        } else {
            span.className = "badge sucesso";
            span.textContent = "Concluído";
            div.appendChild(span);
            div.appendChild(document.createTextNode(" " + mensagemSucesso));
        }
        container.appendChild(div);
    }

    page.executeGeneral = async function () {
        if (executandoGeral) return;
        executandoGeral = true;
        
        try {
            await Phoenix.operations.restorePoint.runProtected(async function () {
                Phoenix.ui.feedback.mostrarOverlay("Aplicando otimização geral...", true);
                try {
                    const jobRes = await Phoenix.bridge.call("executar_otimizacao_geral");
                    if (!jobRes || !jobRes.job_id) { 
                        return; 
                    }
                    const resultado = await Phoenix.jobs.awaitJob(jobRes.job_id);
                    exibirResultadoOtimizacao(resultado, "Otimização geral aplicada.");
                } catch (e) {
                    console.error("[ERRO] Otimização geral:", e);
                } finally {
                    Phoenix.ui.feedback.esconderOverlay(true);
                }
            });
        } finally {
            executandoGeral = false;
        }
    };

    page.executeGaming = async function () {
        if (executandoGaming) return;
        executandoGaming = true;

        try {
            await Phoenix.operations.restorePoint.runProtected(async function () {
                Phoenix.ui.feedback.mostrarOverlay("Aplicando otimização para jogos...", true);
                try {
                    const jobRes = await Phoenix.bridge.call("executar_otimizacao_gaming", false);
                    if (!jobRes || !jobRes.job_id) { 
                        return; 
                    }
                    const resultado = await Phoenix.jobs.awaitJob(jobRes.job_id);
                    exibirResultadoOtimizacao(
                        resultado,
                        "Otimização para jogos aplicada. Reinicie o PC para garantir efeito completo."
                    );
                } catch (e) {
                    console.error("[ERRO] Otimização gaming:", e);
                } finally {
                    Phoenix.ui.feedback.esconderOverlay(true);
                }
            });
        } finally {
            executandoGaming = false;
        }
    };

    page.optimizeDisk = async function () {
        if (executandoDisco) return;
        executandoDisco = true;

        Phoenix.ui.feedback.mostrarOverlay("Otimizando disco — isso pode levar alguns minutos...", true);
        try {
            const jobRes = await Phoenix.bridge.call("otimizar_disco");
            if (!jobRes || !jobRes.job_id) { 
                Phoenix.ui.feedback.esconderOverlay(true); 
                return; 
            }
            const resultado = await Phoenix.jobs.awaitJob(jobRes.job_id);
            Phoenix.ui.feedback.esconderOverlay(true);
            exibirResultadoOtimizacao(resultado, "Otimização de disco concluída.");
        } catch (e) {
            console.error("[ERRO] Otimização disco:", e);
            Phoenix.ui.feedback.esconderOverlay(true);
        } finally {
            executandoDisco = false;
        }
    };

    page.releaseStandbyMemory = async function () {
        if (executandoRam) return;
        executandoRam = true;

        Phoenix.ui.feedback.mostrarOverlay('Liberando memória RAM standby...', true);
        try {
            const jobRes = await Phoenix.bridge.call("liberar_memoria_standby");
            const res = await Phoenix.jobs.awaitJob(jobRes.job_id);
            Phoenix.ui.feedback.esconderOverlay(true, res && res.ok);
        } catch(e) { 
            Phoenix.ui.feedback.esconderOverlay(true, false); 
        } finally {
            executandoRam = false;
        }
    };

    page.analyzeStartup = async function () {
        if (executandoStartup) return;
        executandoStartup = true;

        Phoenix.ui.feedback.mostrarOverlay('Analisando programas de inicialização...');
        try {
            const jobRes = await Phoenix.bridge.call("analisar_startup");
            const res = await Phoenix.jobs.awaitJob(jobRes.job_id);
            Phoenix.ui.feedback.esconderOverlay();
            if (res && res.ok && res.entradas) {
                const container = document.getElementById('resultado-startup');
                if (container) {
                    container.style.display = 'block';
                    container.innerHTML = "";
                    
                    var card = document.createElement("div");
                    card.className = "card";
                    
                    var strong = document.createElement("strong");
                    strong.style.color = "var(--cor-primaria)";
                    strong.textContent = res.entradas.length + " programas encontrados no startup";
                    card.appendChild(strong);
                    
                    var table = document.createElement("table");
                    table.className = "tabela-dados";
                    table.style.marginTop = "16px";
                    
                    var thead = document.createElement("thead");
                    var trHead = document.createElement("tr");
                    var thProg = document.createElement("th");
                    thProg.textContent = "Programa";
                    var thOrig = document.createElement("th");
                    thOrig.textContent = "Origem";
                    trHead.appendChild(thProg);
                    trHead.appendChild(thOrig);
                    thead.appendChild(trHead);
                    table.appendChild(thead);
                    
                    var tbody = document.createElement("tbody");
                    res.entradas.forEach(function(e) {
                        var tr = document.createElement("tr");
                        var tdNome = document.createElement("td");
                        tdNome.textContent = e.nome;
                        var tdRaiz = document.createElement("td");
                        var spanRaiz = document.createElement("span");
                        spanRaiz.className = "badge " + (e.raiz === 'HKLM' ? 'alerta' : 'neutro');
                        spanRaiz.textContent = e.raiz;
                        tdRaiz.appendChild(spanRaiz);
                        tr.appendChild(tdNome);
                        tr.appendChild(tdRaiz);
                        tbody.appendChild(tr);
                    });
                    table.appendChild(tbody);
                    card.appendChild(table);
                    
                    var pHelp = document.createElement("p");
                    pHelp.className = "texto-secundario";
                    pHelp.style.marginTop = "12px";
                    pHelp.textContent = "Use o Gerenciador de Tarefas (Ctrl+Shift+Esc → Inicializar) para desativar programas desnecessários.";
                    card.appendChild(pHelp);
                    
                    container.appendChild(card);
                }
            }
        } catch(e) { 
            Phoenix.ui.feedback.esconderOverlay(); 
        } finally {
            executandoStartup = false;
        }
    };

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.otimizacao = page;

})(window.Phoenix);
