(function (Phoenix) {
    "use strict";

    const page = {};

    function createEl(tag, className, textContent) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (textContent !== undefined) el.textContent = textContent;
        return el;
    }

    function safePct(val) {
        if (val === null || val === undefined || Number.isNaN(val)) return "N/A";
        let num = Number(val);
        if (num < 0) num = 0;
        if (num > 100) num = 100;
        return num;
    }

    // ──────────────────────────────────────────────
    //  Carregar hardware inicial
    // ──────────────────────────────────────────────

    page.carregarHardwareInicial = async function () {
        try {
            var hw = await Phoenix.bridge.call("obter_inventario_atual");

            // Se estiver não carregado
            if (!hw || !hw.status || hw.status === "nao_carregado" || hw.status === "ainda não carregado") {
                atualizarCardsHardware(null); // não mostrar fictícia
                atualizarRodapeMensagem("Iniciando detecção de hardware...");

                // inicia atualização do cache
                const res = await Phoenix.bridge.call("carregar_hardware_cache");
                if (res && res.job_id) {
                    await Phoenix.jobs.awaitJob(res.job_id, (pct, msg) => {
                        atualizarRodapeMensagem(msg);
                    });
                }
                // Refetch after job
                hw = await Phoenix.bridge.call("obter_inventario_atual");
            }

            if (hw && (hw.status === "completo" || hw.status === "parcial" || hw.status === "cache")) {
                Phoenix.state.hardware = hw;

                // Recalcular qualidade visual
                if (Phoenix.ui && Phoenix.ui.visualEffects && typeof Phoenix.ui.visualEffects.refresh === 'function') {
                    Phoenix.ui.visualEffects.refresh();
                }

                atualizarCardsHardware(hw);

                var textoRodape = document.getElementById("texto-rodape");
                if (textoRodape) {
                    textoRodape.textContent =
                        hw.cpu && hw.cpu.modelo
                            ? hw.cpu.modelo
                            : "Hardware detectado";
                }
                var barraRodape = document.getElementById("barra-progresso-rodape");
                if (barraRodape) barraRodape.style.display = "none";
            } else {
                atualizarRodapeMensagem("Estado: " + (hw && hw.status ? hw.status : "falhou"));
                atualizarCardsHardware(null);
            }
        } catch (e) {
            atualizarRodapeMensagem("Erro ao detectar hardware");
        }
    };

    // page.load é chamado pelo router quando a página Início é exibida
    page.load = function () {
        page.carregarHardwareInicial();
        page.iniciarAtualizacaoTempoReal();
    };

    page.leave = function () {
        Phoenix.lifecycle.clearInterval("tempoRealInicio");
        page._atualizandoTempoReal = false;
    };

    function atualizarRodapeMensagem(msg) {
        var textoRodape = document.getElementById("texto-rodape");
        if (textoRodape) textoRodape.textContent = msg;
        var barraRodape = document.getElementById("barra-progresso-rodape");
        if (barraRodape) barraRodape.style.display = "none";
    }

    function atualizarRodapeFalha(msg) {
        atualizarRodapeMensagem(msg);
    }

    // ──────────────────────────────────────────────
    //  Renderização dos cards de hardware (início)
    // ──────────────────────────────────────────────

    function buildCard(id, title, valueStr, unitStr, pct) {
        const card = createEl('div', 'card-metrica');
        card.dataset.card = id;

        card.appendChild(createEl('div', 'rotulo', title));

        const valDiv = createEl('div', 'valor', valueStr);
        if (unitStr) {
            const unitEl = createEl('span', 'unidade', unitStr);
            valDiv.appendChild(unitEl);
        }
        card.appendChild(valDiv);

        if (pct != null) {
            const barContainer = createEl('div', 'barra-progresso');
            const fill = createEl('div', 'preenchimento ' + Phoenix.ui.corPorPercentual(pct));
            fill.style.width = pct + '%';
            barContainer.appendChild(fill);
            card.appendChild(barContainer);
        }

        return card;
    }

    function atualizarCardsHardware(hw) {
        var cards = document.getElementById("cards-resumo-inicio");
        if (!cards) return;

        cards.innerHTML = '';

        // 1. CPU
        const cpuCard = buildCard('cpu', 'CPU', '--', '%', 0);
        cards.appendChild(cpuCard);

        // 2. RAM
        const ramCard = buildCard('ram', 'Memória RAM', '--', '%', 0);
        cards.appendChild(ramCard);

        // 3. GPU
        let nomeGPU = "Não detectada";
        if (hw && hw.gpus && hw.gpus.length > 0) {
            nomeGPU = hw.gpus[0].nome;
        }

        const gpuCard = createEl('div', 'card-metrica');
        gpuCard.dataset.card = 'gpu-uso';
        gpuCard.appendChild(createEl('div', 'rotulo', 'GPU'));
        const valGPU = createEl('div', 'valor', nomeGPU);
        valGPU.style.fontSize = '15px';
        gpuCard.appendChild(valGPU);

        // Espaço reservado para as métricas da GPU que virão via polling
        const gpuMetricasContainer = createEl('div');
        gpuMetricasContainer.className = 'gpu-metrics-container';
        if (hw && hw.capacidades && !hw.capacidades.metricas_gpu_disponiveis) {
            const ind = createEl('div', 'texto-secundario', 'Métricas não suportadas');
            ind.style.fontSize = '11px';
            ind.style.marginTop = '4px';
            gpuMetricasContainer.appendChild(ind);
        }
        gpuCard.appendChild(gpuMetricasContainer);

        cards.appendChild(gpuCard);

        var rodape = document.getElementById("texto-rodape");
        if (rodape && hw && hw.cpu) {
            const ramTotal = hw.memoria ? hw.memoria.total_instalada_gb : "?";
            rodape.textContent = hw.cpu.threads_logicas + ' threads · ' + ramTotal + ' GB RAM';
        }
    }

    // ──────────────────────────────────────────────
    //  Atualização em tempo real (3s)
    // ──────────────────────────────────────────────

    page.iniciarAtualizacaoTempoReal = function () {
        page._atualizandoTempoReal = false;
        Phoenix.lifecycle.setInterval("tempoRealInicio", async function () {
            if (page._atualizandoTempoReal || Phoenix.state.paginaAtual !== "inicio") return;
            page._atualizandoTempoReal = true;
            try {
                // Atualiza CPU e RAM rápidas
                var resRapida = await Phoenix.bridge.call("obter_metricas_rapidas");
                if (Phoenix.state.paginaAtual !== "inicio") {
                    page._atualizandoTempoReal = false;
                    return;
                }
                if (resRapida && resRapida.ok) {
                    atualizarCardsTempoReal({
                        cpu: { uso_percentual: resRapida.cpu_percent },
                        memoria: { percentual_uso: resRapida.ram_percent }
                    });
                }

                // Atualiza GPU
                var hw = Phoenix.state.hardware;
                if (hw && hw.capacidades && hw.capacidades.metricas_gpu_disponiveis) {
                    var resGpu = await Phoenix.bridge.call("obter_gpu_rapida");
                    if (Phoenix.state.paginaAtual !== "inicio") {
                        page._atualizandoTempoReal = false;
                        return;
                    }
                    if (resGpu && resGpu.ok && resGpu.gpu) {
                        atualizarCardGPU(resGpu.gpu);
                    }
                }
            } catch (e) {
                // Silencioso
            }
            page._atualizandoTempoReal = false;
        }, 3000);
    };

    function atualizarCardsTempoReal(dados) {
        var cardCPU = document.querySelector('[data-card="cpu"]');
        var cardRAM = document.querySelector('[data-card="ram"]');

        if (cardCPU && dados.cpu) {
            var pct = safePct(dados.cpu.uso_percentual);
            var cor = pct !== "N/A" ? Phoenix.ui.corPorPercentual(pct) : "";

            // Segurança DOM
            cardCPU.querySelector('.valor').textContent = pct;
            if (pct !== "N/A") {
                const unit = createEl('span', 'unidade', '%');
                cardCPU.querySelector('.valor').appendChild(unit);
            }

            var barra = cardCPU.querySelector('.preenchimento');
            if (barra) {
                barra.style.width = (pct !== "N/A" ? pct : 0) + '%';
                barra.className = 'preenchimento ' + cor;
            }
        }

        if (cardRAM && dados.memoria) {
            var pct = safePct(dados.memoria.percentual_uso);
            var cor = pct !== "N/A" ? Phoenix.ui.corPorPercentual(pct) : "";

            cardRAM.querySelector('.valor').textContent = pct;
            if (pct !== "N/A") {
                const unit = createEl('span', 'unidade', '%');
                cardRAM.querySelector('.valor').appendChild(unit);
            }

            var barra = cardRAM.querySelector('.preenchimento');
            if (barra) {
                barra.style.width = (pct !== "N/A" ? pct : 0) + '%';
                barra.className = 'preenchimento ' + cor;
            }
        }
    }

    function atualizarCardGPU(gpu) {
        var card = document.querySelector('[data-card="gpu-uso"]');
        if (!card) return;

        var container = card.querySelector('.gpu-metrics-container');
        if (!container) return;

        container.innerHTML = '';

        let uso = gpu.uso_percentual;
        if (uso !== null && uso !== undefined && !isNaN(uso)) {
            uso = Math.max(0, Math.min(100, Number(uso)));
            const barContainer = createEl('div', 'barra-progresso');
            const fill = createEl('div', 'preenchimento ' + Phoenix.ui.corPorPercentual(uso));
            fill.style.width = uso + '%';
            barContainer.appendChild(fill);
            container.appendChild(barContainer);

            let txt = uso + '%';
            if (gpu.temperatura_c !== null && gpu.temperatura_c !== undefined && !isNaN(gpu.temperatura_c) && gpu.temperatura_c >= 0) {
                txt += ' · ' + gpu.temperatura_c + '°C';
            } else {
                txt += ' · N/A';
            }

            const sub = createEl('div', 'texto-secundario', txt);
            sub.style.fontSize = '11px';
            sub.style.marginTop = '4px';
            container.appendChild(sub);
        } else {
            const sub = createEl('div', 'texto-secundario', 'N/A');
            sub.style.fontSize = '11px';
            sub.style.marginTop = '4px';
            container.appendChild(sub);
        }
    }

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.inicio = page;
})(window.Phoenix);
