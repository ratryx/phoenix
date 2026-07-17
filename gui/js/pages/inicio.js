(function (Phoenix) {
    "use strict";

    const page = {};
    
    // ──────────────────────────────────────────────
    //  Carregar hardware inicial (cache)
    // ──────────────────────────────────────────────

    page.carregarHardwareInicial = async function () {
        try {
            var jobRes = await Phoenix.bridge.call("carregar_hardware_cache");
            if (jobRes && jobRes.job_id) {
                var hw = await Phoenix.jobs.awaitJob(jobRes.job_id);
                if (hw && hw.ok && hw.hardware) {
                    Phoenix.state.hardware = hw.hardware;
                    atualizarCardsHardware(hw.hardware);

                    var textoRodape = document.getElementById("texto-rodape");
                    if (textoRodape) {
                        textoRodape.textContent =
                            hw.hardware.cpu && hw.hardware.cpu.modelo
                                ? hw.hardware.cpu.modelo
                                : "Hardware detectado";
                    }
                    var barraRodape = document.getElementById("barra-progresso-rodape");
                    if (barraRodape) barraRodape.style.display = "none";
                } else {
                    atualizarRodapeFalha("Hardware não detectado");
                }
            }
        } catch (e) {
            atualizarRodapeFalha("Erro ao detectar hardware");
        }
    };

    function atualizarRodapeFalha(msg) {
        var textoRodape = document.getElementById("texto-rodape");
        if (textoRodape) textoRodape.textContent = msg;
        var barraRodape = document.getElementById("barra-progresso-rodape");
        if (barraRodape) barraRodape.style.display = "none";
    }

    // ──────────────────────────────────────────────
    //  Renderização dos cards de hardware (início)
    // ──────────────────────────────────────────────

    function atualizarCardsHardware(hw) {
        if (!hw) return;
        var cpu = hw.cpu, ram = hw.ram, gpus = hw.gpus || [];
        var cards = document.getElementById("cards-resumo-inicio");
        if (!cards) return;

        var corCPU = Phoenix.ui.corPorPercentual(cpu.uso_percentual);
        var corRAM = Phoenix.ui.corPorPercentual(ram.percentual_uso);
        var nomeGPU = gpus.length > 0 ? gpus[0].nome : 'Não detectada';

        cards.innerHTML =
            '<div class="card-metrica" data-card="cpu">' +
            '<div class="rotulo">CPU</div>' +
            '<div class="valor">' + cpu.uso_percentual + '<span class="unidade">%</span></div>' +
            '<div class="barra-progresso">' +
            '<div class="preenchimento ' + corCPU + '" style="width:' + cpu.uso_percentual + '%"></div>' +
            '</div>' +
            '</div>' +
            '<div class="card-metrica" data-card="ram">' +
            '<div class="rotulo">Memória RAM</div>' +
            '<div class="valor">' + ram.percentual_uso + '<span class="unidade">%</span></div>' +
            '<div class="barra-progresso">' +
            '<div class="preenchimento ' + corRAM + '" style="width:' + ram.percentual_uso + '%"></div>' +
            '</div>' +
            '</div>' +
            '<div class="card-metrica" data-card="gpu-uso">' +
            '<div class="rotulo">GPU</div>' +
            '<div class="valor" style="font-size:15px">' + nomeGPU + '</div>' +
            (gpus.length > 0 && gpus[0].uso_percentual != null ?
                '<div class="barra-progresso">' +
                '<div class="preenchimento ' + Phoenix.ui.corPorPercentual(gpus[0].uso_percentual) +
                '" style="width:' + gpus[0].uso_percentual + '%"></div>' +
                '</div>' +
                '<div style="font-size:11px;color:var(--cor-texto-secundario);margin-top:4px">' +
                gpus[0].uso_percentual + '% · ' +
                (gpus[0].temperatura_c != null ? gpus[0].temperatura_c + '°C' : '') +
                '</div>'
                : '') +
            '</div>';

        var rodape = document.getElementById("texto-rodape");
        if (rodape) {
            rodape.textContent =
                cpu.nucleos_logicos + ' núcleos · ' + ram.total_gb + ' GB RAM';
        }
    }

    // ──────────────────────────────────────────────
    //  Atualização em tempo real (2s)
    // ──────────────────────────────────────────────

    page.iniciarAtualizacaoTempoReal = function () {
        var atualizando = false;
        Phoenix.lifecycle.setInterval("tempoReal", async function () {
            if (atualizando) return;
            atualizando = true;
            try {
                var res = await Phoenix.bridge.call("obter_metricas_rapidas");
                if (res && res.ok) {
                    atualizarCardsTempoReal({
                        cpu: { uso_percentual: res.cpu_percent },
                        memoria: {
                            percentual_uso: res.ram_percent,
                            disponivel_gb: res.ram_disponivel_gb,
                        },
                    });
                }
            } catch (e) {
                // Silencioso
            }
            atualizando = false;
        }, 3000);
    };

    function atualizarCardsTempoReal(dados) {
        var cardCPU = document.querySelector('[data-card="cpu"]');
        var cardRAM = document.querySelector('[data-card="ram"]');

        if (cardCPU && dados.cpu) {
            var pct = dados.cpu.uso_percentual;
            var cor = Phoenix.ui.corPorPercentual(pct);
            cardCPU.querySelector('.valor').innerHTML =
                pct + '<span class="unidade">%</span>';
            var barra = cardCPU.querySelector('.preenchimento');
            if (barra) {
                barra.style.width = pct + '%';
                barra.className = 'preenchimento ' + cor;
            }
        }

        if (cardRAM && dados.memoria) {
            var pct = dados.memoria.percentual_uso;
            var cor = Phoenix.ui.corPorPercentual(pct);
            cardRAM.querySelector('.valor').innerHTML =
                pct + '<span class="unidade">%</span>';
            var barra = cardRAM.querySelector('.preenchimento');
            if (barra) {
                barra.style.width = pct + '%';
                barra.className = 'preenchimento ' + cor;
            }
        }
    }

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.inicio = page;
})(window.Phoenix);
