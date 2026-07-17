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
            iconEl.textContent = "✓";
        } else if (tipo === "erro" || tipo === "alerta") {
            iconEl.textContent = "⚠";
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

    operation.runProtected = async function (acaoFn) {
        if (criandoPonto) return;
        
        if (STATE.restorePointCreatedThisSession) {
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
                STATE.restorePointCreatedThisSession = true;
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
                return new Promise((resolve, reject) => {
                    setTimeout(async () => {
                        const continuar = await confirmarComModalLegado(
                            'Ponto de restauração indisponível',
                            'Não foi possível criar um ponto de restauração do sistema. Deseja continuar com a otimização mesmo assim? Em caso de problemas, não será possível reverter automaticamente.',
                            'alerta'
                        );
                        criandoPonto = false;
                        if (continuar) {
                            STATE.restorePointCreatedThisSession = true;
                            try {
                                const result = await acaoFn();
                                resolve(result);
                            } catch (err) {
                                reject(err);
                            }
                        } else {
                            resolve(undefined);
                        }
                    }, 1300);
                });
            }
        } catch(e) {
            console.error("[ERRO] Ponto de restauração:", e);
            clearInterval(progressoTimer);
            feedback.esconderOverlay(true, false);
            return new Promise((resolve, reject) => {
                setTimeout(async () => {
                    const continuar = await confirmarComModalLegado(
                        'Erro ao criar ponto de restauração',
                        'Ocorreu um erro interno ao tentar criar o ponto de restauração. Deseja continuar com a otimização mesmo assim?',
                        'erro'
                    );
                    criandoPonto = false;
                    if (continuar) {
                        STATE.restorePointCreatedThisSession = true;
                        try {
                            const result = await acaoFn();
                            resolve(result);
                        } catch (err) {
                            reject(err);
                        }
                    } else {
                        resolve(undefined);
                    }
                }, 1300);
            });
        }
    };

    Phoenix.operations = Phoenix.operations || {};
    Phoenix.operations.restorePoint = operation;

})(window.Phoenix);
