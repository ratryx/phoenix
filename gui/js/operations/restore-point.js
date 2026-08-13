(function (Phoenix) {
    "use strict";

    const STATE = Phoenix.state;
    const bridge = Phoenix.bridge;
    const jobs = Phoenix.jobs;
    const feedback = Phoenix.ui.feedback;

    const operation = {};
    let criandoPonto = false;

    // Preserva exatamente a lógica e textos anteriores
    function exibirModalRestauracao(titulo, mensagem, tipo, aoConfirmar, aoCancelar) {
        var modal = document.getElementById("modal-restauracao");
        var tituloEl = document.getElementById("modal-titulo");
        var mensagemEl = document.getElementById("modal-mensagem");
        var iconEl = document.getElementById("modal-icon");
        var btnConfirmar = document.getElementById("btn-modal-confirmar");
        var btnCancelar = document.getElementById("btn-modal-cancelar");

        if (!modal) return;

        tituloEl.textContent = titulo;
        mensagemEl.textContent = mensagem;

        // Reset classes e ícone
        iconEl.className = "modal-status-icon " + tipo;
        if (tipo === "sucesso") {
            iconEl.textContent = "[OK]";
        } else if (tipo === "erro" || tipo === "alerta") {
            iconEl.textContent = "[AVISO]";
        }

        // Ajustar textos dos botões
        if (tipo === "sucesso") {
            btnConfirmar.textContent = "Confirmar e Prosseguir";
            btnConfirmar.className = "botao primario";
        } else {
            btnConfirmar.textContent = "Continuar mesmo assim";
            btnConfirmar.className = "botao primario";
        }
        btnCancelar.textContent = "Cancelar";

        // Garantir botão confirmar visível
        btnConfirmar.style.display = "";

        // Event handlers (com remoção automática)
        function cliqueConfirmar() {
            modal.classList.remove("visivel");
            desregistrar();
            aoConfirmar();
        }

        function cliqueCancelar() {
            modal.classList.remove("visivel");
            desregistrar();
            aoCancelar();
        }

        function desregistrar() {
            btnConfirmar.removeEventListener("click", cliqueConfirmar);
            btnCancelar.removeEventListener("click", cliqueCancelar);
        }

        btnConfirmar.addEventListener("click", cliqueConfirmar);
        btnCancelar.addEventListener("click", cliqueCancelar);

        modal.classList.add("visivel");
    }

    function confirmarComModalLegado(titulo, mensagem, tipo) {
        return new Promise((resolve) => {
            exibirModalRestauracao(
                titulo,
                mensagem,
                tipo,
                () => resolve(true),
                () => resolve(false)
            );
        });
    }

    function exibirModalRiscoRestore(motivo) {
        return new Promise((resolve) => {
            var modal = document.getElementById("modal-risco-restauracao");
            if (!modal) {
                // Fallback in case HTML not present
                console.error("[ERRO FATAL] Modal de risco de restauração não encontrado no DOM. Abortando operação por segurança.");
                resolve('cancelar');
                return;
            }
            
            var motivoEl = document.getElementById("modal-risco-motivo");
            motivoEl.textContent = motivo || "Falha desconhecida.";

            var btnAbrir = document.getElementById("btn-modal-risco-abrir");
            var btnTentar = document.getElementById("btn-modal-risco-tentar");
            var btnContinuar = document.getElementById("btn-modal-risco-continuar");
            var btnCancelar = document.getElementById("btn-modal-risco-cancelar");

            function closeAndResolve(action) {
                modal.classList.remove("visivel");
                btnAbrir.removeEventListener("click", onAbrir);
                btnTentar.removeEventListener("click", onTentar);
                btnContinuar.removeEventListener("click", onContinuar);
                btnCancelar.removeEventListener("click", onCancelar);
                resolve(action);
            }

            function onAbrir() { closeAndResolve('abrir'); }
            function onTentar() { closeAndResolve('tentar'); }
            function onContinuar() { closeAndResolve('continuar'); }
            function onCancelar() { closeAndResolve('cancelar'); }

            btnAbrir.addEventListener("click", onAbrir);
            btnTentar.addEventListener("click", onTentar);
            btnContinuar.addEventListener("click", onContinuar);
            btnCancelar.addEventListener("click", onCancelar);

            modal.classList.add("visivel");
        });
    }

    operation.runProtected = async function (acaoFn) {
        if (criandoPonto) return;
        
        if (STATE.protectionState === 'restore_created' || STATE.protectionState === 'risk_accepted') {
            return await acaoFn();
        }

        criandoPonto = true;
        feedback.mostrarOverlay('Criando ponto de restauração...', true);
        
        // Simular progresso enquanto o PowerShell roda
        feedback.atualizarOverlay('Invocando PowerShell...', 10);
        
        const progressoTimer = setInterval(() => {
            const fill = document.getElementById('overlay-barra-fill');
            if (fill && !fill.classList.contains('indeterminado')) {
                const atual = parseFloat(fill.style.width) || 10;
                if (atual < 85) {
                    feedback.atualizarOverlay('Criando ponto de restauração do sistema...', atual + 5);
                }
            }
        }, 2000);
        
        try {
            const jobRes = await bridge.call("criar_ponto_restauracao");
            if (!jobRes || !jobRes.job_id) {
                // Falha de bridge sem job
                clearInterval(progressoTimer);
                throw new Error("Falha ao iniciar criação do ponto");
            }
            
            const res = await jobs.awaitJob(jobRes.job_id);
            clearInterval(progressoTimer);
            
            if (res && res.ok) {
                STATE.protectionState = 'restore_created';
                feedback.atualizarOverlay('Ponto de restauração criado!', 100);
                
                return new Promise((resolve, reject) => {
                    setTimeout(async () => {
                        feedback.esconderOverlay(true, true);
                        criandoPonto = false;
                        try {
                            const result = await acaoFn();
                            resolve(result);
                        } catch (err) {
                            reject(err);
                        }
                    }, 800);
                });
            } else {
                feedback.esconderOverlay(true, false);
                return handleRestoreFailure(res ? res.erro : "Falha desconhecida", acaoFn);
            }
        } catch(e) {
            console.error("[ERRO] Ponto de restauração:", e);
            clearInterval(progressoTimer);
            feedback.esconderOverlay(true, true);
            return handleRestoreFailure("Ocorreu um erro interno ao tentar criar o ponto de restauração.", acaoFn);
        }
    };

    async function handleRestoreFailure(erroMsg, acaoFn) {
        criandoPonto = false;
        
        while (true) {
            const action = await exibirModalRiscoRestore(erroMsg);
            
            if (action === 'cancelar') {
                return undefined;
            } else if (action === 'abrir') {
                try {
                    await bridge.call("abrir_protecao_sistema");
                } catch (err) {
                    console.error("Falha ao abrir sysdm.cpl", err);
                }
                // Continues the loop, allowing them to retry or continue
            } else if (action === 'tentar') {
                return await operation.runProtected(acaoFn);
            } else if (action === 'continuar') {
                try {
                    const confirmacao = await bridge.call("confirmar_risco_protecao");
                    if (confirmacao && confirmacao.ok) {
                        STATE.protectionState = 'risk_accepted';
                        return await acaoFn();
                    } else {
                        return undefined;
                    }
                } catch (e) {
                    console.error("[ERRO] Falha ao confirmar risco:", e);
                    return undefined;
                }
            }
        }
    }

    Phoenix.operations = Phoenix.operations || {};
    Phoenix.operations.restorePoint = operation;

})(window.Phoenix);
