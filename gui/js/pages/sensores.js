(function (Phoenix) {
    "use strict";

    const page = {};
    let atualizando = false;

    page.load = async function () {
        var container = document.getElementById('pagina-hwmonitor');
        if (!container) return;
        var hw = Phoenix.state.hardware;
        if (!hw) return;

        var gpus = hw.gpus || [];
        var gpuNome = gpus.length > 0 ? gpus[0].nome : 'GPU';
        
        container.innerHTML =
            '<div class="cabecalho-pagina">' +
            '<div>' +
            '<h1>Monitor de Sensores</h1>' +
            '<p>Monitoramento em tempo real — atualiza a cada 3s</p>' +
            '</div>' +
            '</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">' +
            
            '<!-- CPU -->' +
            '<div class="card">' +
            '<div style="color:var(--cor-primaria);font-weight:600;margin-bottom:12px">CPU</div>' +
            '<div style="font-size:36px;font-weight:700" id="hw-cpu-total">--<span style="font-size:16px">%</span></div>' +
            '<div class="barra-progresso" style="margin:8px 0">' +
            '<div class="preenchimento" id="hw-cpu-bar" style="width:0%;transition:width 0.5s"></div>' +
            '</div>' +
            '<div class="texto-secundario" id="hw-cpu-freq">-- MHz</div>' +
            '<div style="margin-top:16px">' +
            '<div style="font-size:11px;color:var(--cor-texto-terciario);text-transform:uppercase;margin-bottom:8px">Por núcleo</div>' +
            '<div id="hw-nucleos" style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px"></div>' +
            '</div>' +
            '</div>' +

            '<!-- GPU -->' +
            '<div class="card">' +
            '<div style="color:var(--cor-primaria);font-weight:600;margin-bottom:12px" id="hw-gpu-nome">' + gpuNome + '</div>' +
            '<div style="font-size:36px;font-weight:700" id="hw-gpu-uso">--<span style="font-size:16px">%</span></div>' +
            '<div class="barra-progresso" style="margin:8px 0">' +
            '<div class="preenchimento" id="hw-gpu-bar" style="width:0%;transition:width 0.5s"></div>' +
            '</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px">' +
            '<div class="card-metrica" style="padding:12px">' +
            '<div class="rotulo">Temperatura</div>' +
            '<div class="valor" id="hw-gpu-temp" style="font-size:20px">--°C</div>' +
            '</div>' +
            '<div class="card-metrica" style="padding:12px">' +
            '<div class="rotulo">VRAM</div>' +
            '<div class="valor" id="hw-gpu-vram" style="font-size:16px">-- / -- MB</div>' +
            '</div>' +
            '</div>' +
            '</div>' +

            '<!-- RAM -->' +
            '<div class="card">' +
            '<div style="color:var(--cor-primaria);font-weight:600;margin-bottom:12px">Memória RAM</div>' +
            '<div style="font-size:36px;font-weight:700" id="hw-ram-pct">--<span style="font-size:16px">%</span></div>' +
            '<div class="barra-progresso" style="margin:8px 0">' +
            '<div class="preenchimento" id="hw-ram-bar" style="width:0%;transition:width 0.5s"></div>' +
            '</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px">' +
            '<div class="card-metrica" style="padding:12px">' +
            '<div class="rotulo">Em uso</div>' +
            '<div class="valor" id="hw-ram-usada" style="font-size:18px">-- GB</div>' +
            '</div>' +
            '<div class="card-metrica" style="padding:12px">' +
            '<div class="rotulo">Disponível</div>' +
            '<div class="valor" id="hw-ram-livre" style="font-size:18px">-- GB</div>' +
            '</div>' +
            '</div>' +
            '</div>' +

            '<!-- Disco I/O -->' +
            '<div class="card">' +
            '<div style="color:var(--cor-primaria);font-weight:600;margin-bottom:12px">Disco — Atividade em tempo real</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:8px">' +
            '<div>' +
            '<div class="texto-secundario">Leitura</div>' +
            '<div style="font-size:28px;font-weight:700;color:var(--cor-info)" id="hw-disk-read">--<span style="font-size:13px"> MB/s</span></div>' +
            '</div>' +
            '<div>' +
            '<div class="texto-secundario">Escrita</div>' +
            '<div style="font-size:28px;font-weight:700;color:var(--cor-alerta)" id="hw-disk-write">--<span style="font-size:13px"> MB/s</span></div>' +
            '</div>' +
            '</div>' +
            '</div>' +

            '</div>';

        page.enter();
    };

    page.enter = function() {
        Phoenix.lifecycle.clearInterval("sensores");
        page.atualizar(); // Primeira carga
        Phoenix.lifecycle.setInterval("sensores", page.atualizar, 3000);
    };

    page.atualizar = async function () {
        if (atualizando || Phoenix.state.paginaAtual !== "hwmonitor") return;
        atualizando = true;
        try {
            var res = await Phoenix.bridge.call("obter_metricas_completas");
            if (!res || !res.ok) return;

            // Atualiza CPU
            var cpuVal = document.getElementById('hw-cpu-total');
            var cpuBar = document.getElementById('hw-cpu-bar');
            var cpuFreq = document.getElementById('hw-cpu-freq');
            
            if (cpuVal) cpuVal.innerHTML = res.cpu.total + '<span style="font-size:16px">%</span>';
            if (cpuBar) {
                cpuBar.style.width = res.cpu.total + '%';
                cpuBar.className = 'preenchimento ' + Phoenix.ui.corPorPercentual(res.cpu.total);
            }
            if (cpuFreq) cpuFreq.textContent = res.cpu.freq_mhz ? res.cpu.freq_mhz + ' MHz' : '-- MHz';
            
            var nucleosEl = document.getElementById('hw-nucleos');
            if (nucleosEl && res.cpu.por_nucleo) {
                nucleosEl.innerHTML = res.cpu.por_nucleo.map(function(pct, i) {
                    var cor = pct > 90 ? 'var(--cor-erro)' : pct > 70 ? 'var(--cor-alerta)' : 'var(--cor-texto)';
                    return '<div style="text-align:center">' +
                        '<div style="font-size:10px;color:var(--cor-texto-terciario)">C' + (i+1) + '</div>' +
                        '<div style="font-size:13px;font-weight:600;color:' + cor + '">' + pct + '%</div>' +
                        '</div>';
                }).join('');
            }

            // Atualiza RAM
            var ramPct = document.getElementById('hw-ram-pct');
            var ramBar = document.getElementById('hw-ram-bar');
            var ramUsada = document.getElementById('hw-ram-usada');
            var ramLivre = document.getElementById('hw-ram-livre');

            if (ramPct) ramPct.innerHTML = res.ram.percent + '<span style="font-size:16px">%</span>';
            if (ramBar) {
                ramBar.style.width = res.ram.percent + '%';
                ramBar.className = 'preenchimento ' + Phoenix.ui.corPorPercentual(res.ram.percent);
            }
            if (ramUsada) ramUsada.textContent = res.ram.usada_gb + ' GB';
            if (ramLivre) ramLivre.textContent = res.ram.disponivel_gb + ' GB';

            // Atualiza GPU
            var gpuUso = document.getElementById('hw-gpu-uso');
            var gpuBar = document.getElementById('hw-gpu-bar');
            var gpuTemp = document.getElementById('hw-gpu-temp');
            var gpuVram = document.getElementById('hw-gpu-vram');

            if (res.gpu) {
                var g = res.gpu;
                if (gpuUso) gpuUso.innerHTML = g.uso + '<span style="font-size:16px">%</span>';
                if (gpuBar) {
                    gpuBar.style.width = g.uso + '%';
                    gpuBar.className = 'preenchimento ' + Phoenix.ui.corPorPercentual(g.uso);
                }
                if (gpuTemp) {
                    var corTemp = g.temp >= 85 ? 'var(--cor-erro)' : g.temp >= 70 ? 'var(--cor-alerta)' : 'var(--cor-sucesso)';
                    gpuTemp.innerHTML = '<span style="color:' + corTemp + '">' + g.temp + '°C</span>';
                }
                if (gpuVram) gpuVram.textContent = g.vram_usada + ' / ' + g.vram_total + ' MB';
            }

            // Atualiza Disco I/O
            var diskRead = document.getElementById('hw-disk-read');
            var diskWrite = document.getElementById('hw-disk-write');
            
            if (diskRead) diskRead.innerHTML = res.disco.leitura_mb + '<span style="font-size:13px"> MB/s</span>';
            if (diskWrite) diskWrite.innerHTML = res.disco.escrita_mb + '<span style="font-size:13px"> MB/s</span>';

        } catch (e) {
            console.error("Erro no hwmonitor:", e);
        } finally {
            atualizando = false;
        }
    };

    page.leave = function () {
        Phoenix.lifecycle.clearInterval("sensores");
        atualizando = false;
    };

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.hwmonitor = page;

})(window.Phoenix);
