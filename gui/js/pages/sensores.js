(function (Phoenix) {
    "use strict";

    const page = {};
    let atualizando = false;

    function createEl(tag, className, textContent) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (textContent !== undefined) el.textContent = textContent;
        return el;
    }

    page.load = async function () {
        var container = document.getElementById('pagina-hwmonitor');
        if (!container) return;
        var hw = Phoenix.state.hardware;
        
        container.innerHTML = '';
        
        const header = createEl('div', 'cabecalho-pagina');
        const hTitleDiv = createEl('div');
        hTitleDiv.appendChild(createEl('h1', '', 'Monitor de Sensores'));
        hTitleDiv.appendChild(createEl('p', '', 'Monitoramento em tempo real — atualiza a cada 3s'));
        header.appendChild(hTitleDiv);
        container.appendChild(header);
        
        const grid = createEl('div');
        grid.style.display = 'grid';
        grid.style.gridTemplateColumns = '1fr 1fr';
        grid.style.gap = '16px';
        
        // 1. CPU
        const cpuCard = createEl('div', 'card');
        const cpuTitle = createEl('div', '', 'CPU');
        cpuTitle.style.color = 'var(--cor-primaria)';
        cpuTitle.style.fontWeight = '600';
        cpuTitle.style.marginBottom = '12px';
        cpuCard.appendChild(cpuTitle);
        
        const cpuTotal = createEl('div', '', '--');
        cpuTotal.style.fontSize = '36px';
        cpuTotal.style.fontWeight = '700';
        cpuTotal.id = 'hw-cpu-total';
        const cpuUnit = createEl('span', '', '%');
        cpuUnit.style.fontSize = '16px';
        cpuTotal.appendChild(cpuUnit);
        cpuCard.appendChild(cpuTotal);
        
        const cpuBarCont = createEl('div', 'barra-progresso');
        cpuBarCont.style.margin = '8px 0';
        const cpuBar = createEl('div', 'preenchimento');
        cpuBar.id = 'hw-cpu-bar';
        cpuBar.style.width = '0%';
        cpuBar.style.transition = 'width 0.5s';
        cpuBarCont.appendChild(cpuBar);
        cpuCard.appendChild(cpuBarCont);
        
        const cpuFreq = createEl('div', 'texto-secundario', '-- MHz');
        cpuFreq.id = 'hw-cpu-freq';
        cpuCard.appendChild(cpuFreq);
        
        const cpuCoresDiv = createEl('div');
        cpuCoresDiv.style.marginTop = '16px';
        const cpuCoresLabel = createEl('div', 'texto-secundario', 'POR NÚCLEO');
        cpuCoresLabel.style.fontSize = '11px';
        cpuCoresLabel.style.textTransform = 'uppercase';
        cpuCoresLabel.style.marginBottom = '8px';
        cpuCoresDiv.appendChild(cpuCoresLabel);
        
        const coresGrid = createEl('div');
        coresGrid.id = 'hw-nucleos';
        coresGrid.style.display = 'grid';
        coresGrid.style.gridTemplateColumns = 'repeat(4, 1fr)';
        coresGrid.style.gap = '6px';
        cpuCoresDiv.appendChild(coresGrid);
        cpuCard.appendChild(cpuCoresDiv);
        
        grid.appendChild(cpuCard);
        
        // 2. RAM
        const ramCard = createEl('div', 'card');
        const ramTitle = createEl('div', '', 'Memória RAM');
        ramTitle.style.color = 'var(--cor-primaria)';
        ramTitle.style.fontWeight = '600';
        ramTitle.style.marginBottom = '12px';
        ramCard.appendChild(ramTitle);
        
        const ramPct = createEl('div', '', '--');
        ramPct.style.fontSize = '36px';
        ramPct.style.fontWeight = '700';
        ramPct.id = 'hw-ram-pct';
        const ramUnit = createEl('span', '', '%');
        ramUnit.style.fontSize = '16px';
        ramPct.appendChild(ramUnit);
        ramCard.appendChild(ramPct);
        
        const ramBarCont = createEl('div', 'barra-progresso');
        ramBarCont.style.margin = '8px 0';
        const ramBar = createEl('div', 'preenchimento');
        ramBar.id = 'hw-ram-bar';
        ramBar.style.width = '0%';
        ramBar.style.transition = 'width 0.5s';
        ramBarCont.appendChild(ramBar);
        ramCard.appendChild(ramBarCont);
        
        const ramMetrics = createEl('div');
        ramMetrics.style.display = 'grid';
        ramMetrics.style.gridTemplateColumns = '1fr 1fr';
        ramMetrics.style.gap = '8px';
        ramMetrics.style.marginTop = '12px';
        
        const ramU = createEl('div', 'card-metrica');
        ramU.style.padding = '12px';
        ramU.appendChild(createEl('div', 'rotulo', 'Em uso'));
        const ramUVal = createEl('div', 'valor', '-- GB');
        ramUVal.id = 'hw-ram-usada';
        ramUVal.style.fontSize = '18px';
        ramU.appendChild(ramUVal);
        ramMetrics.appendChild(ramU);
        
        const ramL = createEl('div', 'card-metrica');
        ramL.style.padding = '12px';
        ramL.appendChild(createEl('div', 'rotulo', 'Disponível'));
        const ramLVal = createEl('div', 'valor', '-- GB');
        ramLVal.id = 'hw-ram-livre';
        ramLVal.style.fontSize = '18px';
        ramL.appendChild(ramLVal);
        ramMetrics.appendChild(ramL);
        
        ramCard.appendChild(ramMetrics);
        grid.appendChild(ramCard);
        
        // 3. Disco I/O
        const diskCard = createEl('div', 'card');
        const diskTitle = createEl('div', '', 'Disco — Atividade em tempo real');
        diskTitle.style.color = 'var(--cor-primaria)';
        diskTitle.style.fontWeight = '600';
        diskTitle.style.marginBottom = '12px';
        diskCard.appendChild(diskTitle);
        
        const diskMetrics = createEl('div');
        diskMetrics.style.display = 'grid';
        diskMetrics.style.gridTemplateColumns = '1fr 1fr';
        diskMetrics.style.gap = '16px';
        diskMetrics.style.marginTop = '8px';
        
        const dRead = createEl('div');
        dRead.appendChild(createEl('div', 'texto-secundario', 'Leitura'));
        const dReadVal = createEl('div', '', '--');
        dReadVal.id = 'hw-disk-read';
        dReadVal.style.fontSize = '28px';
        dReadVal.style.fontWeight = '700';
        dReadVal.style.color = 'var(--cor-info)';
        const dReadU = createEl('span', '', ' MB/s');
        dReadU.style.fontSize = '13px';
        dReadVal.appendChild(dReadU);
        dRead.appendChild(dReadVal);
        diskMetrics.appendChild(dRead);
        
        const dWrite = createEl('div');
        dWrite.appendChild(createEl('div', 'texto-secundario', 'Escrita'));
        const dWriteVal = createEl('div', '', '--');
        dWriteVal.id = 'hw-disk-write';
        dWriteVal.style.fontSize = '28px';
        dWriteVal.style.fontWeight = '700';
        dWriteVal.style.color = 'var(--cor-alerta)';
        const dWriteU = createEl('span', '', ' MB/s');
        dWriteU.style.fontSize = '13px';
        dWriteVal.appendChild(dWriteU);
        dWrite.appendChild(dWriteVal);
        diskMetrics.appendChild(dWrite);
        
        diskCard.appendChild(diskMetrics);
        grid.appendChild(diskCard);
        
        // 4. GPUs - container to be populated dynamically
        const gpusContainer = createEl('div');
        gpusContainer.id = 'hw-gpus-container';
        // Will place it below the main grid, or inside it if fits
        
        container.appendChild(grid);
        container.appendChild(gpusContainer);

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
            
            if (cpuVal) {
                cpuVal.textContent = res.cpu.uso_percentual;
                const un = createEl('span', '', '%');
                un.style.fontSize = '16px';
                cpuVal.appendChild(un);
            }
            if (cpuBar) {
                cpuBar.style.width = res.cpu.uso_percentual + '%';
                cpuBar.className = 'preenchimento ' + Phoenix.ui.corPorPercentual(res.cpu.uso_percentual);
            }
            if (cpuFreq) cpuFreq.textContent = res.cpu.frequencia_atual_mhz ? res.cpu.frequencia_atual_mhz + ' MHz' : '-- MHz';
            
            var nucleosEl = document.getElementById('hw-nucleos');
            if (nucleosEl && res.cpu.uso_por_nucleo) {
                nucleosEl.innerHTML = ''; // Limpa seguro
                res.cpu.uso_por_nucleo.forEach((pct, i) => {
                    var cor = pct > 90 ? 'var(--cor-erro)' : pct > 70 ? 'var(--cor-alerta)' : 'var(--cor-texto)';
                    const nd = createEl('div');
                    nd.style.textAlign = 'center';
                    const nTitle = createEl('div', 'texto-secundario', 'C' + (i+1));
                    nTitle.style.fontSize = '10px';
                    const nPct = createEl('div', '', pct + '%');
                    nPct.style.fontSize = '13px';
                    nPct.style.fontWeight = '600';
                    nPct.style.color = cor;
                    nd.appendChild(nTitle);
                    nd.appendChild(nPct);
                    nucleosEl.appendChild(nd);
                });
            }

            // Atualiza RAM
            var ramPct = document.getElementById('hw-ram-pct');
            var ramBar = document.getElementById('hw-ram-bar');
            var ramUsada = document.getElementById('hw-ram-usada');
            var ramLivre = document.getElementById('hw-ram-livre');

            if (ramPct) {
                ramPct.textContent = res.memoria.percentual_uso;
                const un = createEl('span', '', '%');
                un.style.fontSize = '16px';
                ramPct.appendChild(un);
            }
            if (ramBar) {
                ramBar.style.width = res.memoria.percentual_uso + '%';
                ramBar.className = 'preenchimento ' + Phoenix.ui.corPorPercentual(res.memoria.percentual_uso);
            }
            if (ramUsada) ramUsada.textContent = res.memoria.usada_gb + ' GB';
            if (ramLivre) ramLivre.textContent = res.memoria.disponivel_gb + ' GB';

            // Atualiza Disco I/O
            var diskRead = document.getElementById('hw-disk-read');
            var diskWrite = document.getElementById('hw-disk-write');
            
            if (diskRead) {
                diskRead.textContent = res.disco.leitura_mb_s;
                const un = createEl('span', '', ' MB/s');
                un.style.fontSize = '13px';
                diskRead.appendChild(un);
            }
            if (diskWrite) {
                diskWrite.textContent = res.disco.escrita_mb_s;
                const un = createEl('span', '', ' MB/s');
                un.style.fontSize = '13px';
                diskWrite.appendChild(un);
            }
            
            // Atualiza GPUs
            var gpusContainer = document.getElementById('hw-gpus-container');
            if (gpusContainer) {
                gpusContainer.innerHTML = ''; // refaz a cada tick pra suportar N gpus seguras
                gpusContainer.style.marginTop = '16px';
                
                if (!res.gpus || res.gpus.length === 0) {
                    const noGpuCard = createEl('div', 'card');
                    const noGpuText = createEl('div', 'texto-secundario', 'Métricas de GPU não suportadas ou não disponíveis.');
                    noGpuCard.appendChild(noGpuText);
                    gpusContainer.appendChild(noGpuCard);
                } else {
                    res.gpus.forEach((g) => {
                        const gc = createEl('div', 'card');
                        gc.style.marginBottom = '16px';
                        
                        const gt = createEl('div', '', g.nome || 'GPU');
                        gt.style.color = 'var(--cor-primaria)';
                        gt.style.fontWeight = '600';
                        gt.style.marginBottom = '12px';
                        gc.appendChild(gt);
                        
                        const gu = createEl('div', '', String(g.uso_percentual));
                        gu.style.fontSize = '36px';
                        gu.style.fontWeight = '700';
                        const guu = createEl('span', '', '%');
                        guu.style.fontSize = '16px';
                        gu.appendChild(guu);
                        gc.appendChild(gu);
                        
                        const gb = createEl('div', 'barra-progresso');
                        gb.style.margin = '8px 0';
                        const gbf = createEl('div', 'preenchimento ' + Phoenix.ui.corPorPercentual(g.uso_percentual));
                        gbf.style.width = g.uso_percentual + '%';
                        gbf.style.transition = 'width 0.5s';
                        gb.appendChild(gbf);
                        gc.appendChild(gb);
                        
                        const gm = createEl('div');
                        gm.style.display = 'grid';
                        gm.style.gridTemplateColumns = '1fr 1fr';
                        gm.style.gap = '8px';
                        gm.style.marginTop = '12px';
                        
                        const gmt = createEl('div', 'card-metrica');
                        gmt.style.padding = '12px';
                        gmt.appendChild(createEl('div', 'rotulo', 'Temperatura'));
                        
                        let tempTxt = '--°C';
                        let corTemp = '';
                        if (g.temperatura_c > 0) {
                            tempTxt = g.temperatura_c + '°C';
                            corTemp = g.temperatura_c >= 85 ? 'var(--cor-erro)' : g.temperatura_c >= 70 ? 'var(--cor-alerta)' : 'var(--cor-sucesso)';
                        } else {
                            tempTxt = 'N/A';
                        }
                        
                        const gmtv = createEl('div', 'valor', tempTxt);
                        gmtv.style.fontSize = '20px';
                        if (corTemp) gmtv.style.color = corTemp;
                        gmt.appendChild(gmtv);
                        gm.appendChild(gmt);
                        
                        const gmv = createEl('div', 'card-metrica');
                        gmv.style.padding = '12px';
                        gmv.appendChild(createEl('div', 'rotulo', 'VRAM'));
                        const gmvv = createEl('div', 'valor', `${g.vram_usada_mb} / ${g.vram_total_mb} MB`);
                        gmvv.style.fontSize = '16px';
                        gmv.appendChild(gmvv);
                        gm.appendChild(gmv);
                        
                        gc.appendChild(gm);
                        gpusContainer.appendChild(gc);
                    });
                }
            }

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
