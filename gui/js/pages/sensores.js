(function (Phoenix) {
    "use strict";

    const page = {};
    let atualizando = false;
    let _reqId = 0;
    let _gpusRenderizadas = [];

    function safeVal(val, defaultVal = "N/A") {
        if (val === null || val === undefined || Number.isNaN(val)) return defaultVal;
        return val;
    }

    function safePct(val) {
        if (val === null || val === undefined || Number.isNaN(val)) return "N/A";
        let num = Number(val);
        if (num < 0) num = 0;
        if (num > 100) num = 100;
        return num;
    }

    function createEl(tag, className, textContent) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (textContent !== undefined) el.textContent = textContent;
        return el;
    }

    page.load = async function () {
        var container = document.getElementById('pagina-hwmonitor');
        if (!container) return;
        
        container.innerHTML = '';
        _gpusRenderizadas = [];
        
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
        
        // 4. GPUs - container
        const gpusContainer = createEl('div');
        gpusContainer.id = 'hw-gpus-container';
        gpusContainer.style.marginTop = '16px';
        
        container.appendChild(grid);
        container.appendChild(gpusContainer);

        page.enter();
    };

    page.enter = function() {
        Phoenix.lifecycle.clearInterval("sensores");
        _reqId++;
        page.atualizar(); // Primeira carga
        Phoenix.lifecycle.setInterval("sensores", page.atualizar, 3000);
    };

    page.atualizar = async function () {
        if (atualizando || Phoenix.state.paginaAtual !== "hwmonitor") return;
        atualizando = true;
        const currentReq = _reqId;
        try {
            var res = await Phoenix.bridge.call("obter_metricas_completas");
            if (currentReq !== _reqId || Phoenix.state.paginaAtual !== "hwmonitor") return;
            if (!res || !res.ok) return;

            // CPU
            if (res.cpu) {
                var cpuVal = document.getElementById('hw-cpu-total');
                var cpuBar = document.getElementById('hw-cpu-bar');
                var cpuFreq = document.getElementById('hw-cpu-freq');
                
                if (cpuVal) {
                    const valPct = safePct(res.cpu.uso_percentual);
                    cpuVal.textContent = valPct;
                    if (valPct !== "N/A") {
                        const un = createEl('span', '', '%');
                        un.style.fontSize = '16px';
                        cpuVal.appendChild(un);
                        if (cpuBar) {
                            cpuBar.style.width = valPct + '%';
                            cpuBar.className = 'preenchimento ' + Phoenix.ui.corPorPercentual(valPct);
                        }
                    } else if (cpuBar) {
                        cpuBar.style.width = '0%';
                        cpuBar.className = 'preenchimento';
                    }
                }
                if (cpuFreq) {
                    let freq = safeVal(res.cpu.frequencia_atual_mhz);
                    cpuFreq.textContent = freq !== "N/A" ? freq + ' MHz' : 'N/A';
                }
                
                var nucleosEl = document.getElementById('hw-nucleos');
                if (nucleosEl && res.cpu.uso_por_nucleo && Array.isArray(res.cpu.uso_por_nucleo)) {
                    // Update instead of clear if counts match
                    const existingCount = nucleosEl.children.length;
                    if (existingCount !== res.cpu.uso_por_nucleo.length) {
                        nucleosEl.innerHTML = '';
                        res.cpu.uso_por_nucleo.forEach((_, i) => {
                            const nd = createEl('div');
                            nd.style.textAlign = 'center';
                            const nTitle = createEl('div', 'texto-secundario', 'C' + (i+1));
                            nTitle.style.fontSize = '10px';
                            const nPct = createEl('div');
                            nPct.style.fontSize = '13px';
                            nPct.style.fontWeight = '600';
                            nd.appendChild(nTitle);
                            nd.appendChild(nPct);
                            nucleosEl.appendChild(nd);
                        });
                    }
                    res.cpu.uso_por_nucleo.forEach((pctRaw, i) => {
                        const pct = safePct(pctRaw);
                        if (pct === "N/A") return;
                        const nPct = nucleosEl.children[i].children[1];
                        var cor = pct > 90 ? 'var(--cor-erro)' : pct > 70 ? 'var(--cor-alerta)' : 'var(--cor-texto)';
                        nPct.textContent = pct + '%';
                        nPct.style.color = cor;
                    });
                }
            }

            // RAM
            if (res.memoria) {
                var ramPct = document.getElementById('hw-ram-pct');
                var ramBar = document.getElementById('hw-ram-bar');
                var ramUsada = document.getElementById('hw-ram-usada');
                var ramLivre = document.getElementById('hw-ram-livre');

                if (ramPct) {
                    const valPct = safePct(res.memoria.percentual_uso);
                    ramPct.textContent = valPct;
                    if (valPct !== "N/A") {
                        const un = createEl('span', '', '%');
                        un.style.fontSize = '16px';
                        ramPct.appendChild(un);
                        if (ramBar) {
                            ramBar.style.width = valPct + '%';
                            ramBar.className = 'preenchimento ' + Phoenix.ui.corPorPercentual(valPct);
                        }
                    } else if (ramBar) {
                        ramBar.style.width = '0%';
                        ramBar.className = 'preenchimento';
                    }
                }
                if (ramUsada) {
                    let u = safeVal(res.memoria.usada_gb);
                    ramUsada.textContent = u !== "N/A" ? u + ' GB' : 'N/A';
                }
                if (ramLivre) {
                    let l = safeVal(res.memoria.disponivel_gb);
                    ramLivre.textContent = l !== "N/A" ? l + ' GB' : 'N/A';
                }
            }

            // Disco I/O
            if (res.disco) {
                var diskRead = document.getElementById('hw-disk-read');
                var diskWrite = document.getElementById('hw-disk-write');
                
                if (diskRead) {
                    let r = safeVal(res.disco.leitura_mb_s);
                    diskRead.textContent = r;
                    if (r !== "N/A") {
                        const un = createEl('span', '', ' MB/s');
                        un.style.fontSize = '13px';
                        diskRead.appendChild(un);
                    }
                }
                if (diskWrite) {
                    let w = safeVal(res.disco.escrita_mb_s);
                    diskWrite.textContent = w;
                    if (w !== "N/A") {
                        const un = createEl('span', '', ' MB/s');
                        un.style.fontSize = '13px';
                        diskWrite.appendChild(un);
                    }
                }
            }
            
            // GPUs
            var gpusContainer = document.getElementById('hw-gpus-container');
            if (gpusContainer) {
                let gpusToProcess = [];
                if (res.gpus && Array.isArray(res.gpus)) {
                    gpusToProcess = res.gpus;
                }
                
                // Compare IDs to see if we need a rebuild
                const incomingIds = gpusToProcess.map((g, i) => String(safeVal(g.id, "gpu_"+i))).join("|");
                const currentIds = _gpusRenderizadas.join("|");
                
                if (incomingIds !== currentIds) {
                    // Rebuild
                    gpusContainer.innerHTML = '';
                    _gpusRenderizadas = gpusToProcess.map((g, i) => String(safeVal(g.id, "gpu_"+i)));
                    
                    if (gpusToProcess.length === 0) {
                        const noGpuCard = createEl('div', 'card');
                        const noGpuText = createEl('div', 'texto-secundario', 'Métricas de GPU não suportadas ou não disponíveis.');
                        noGpuCard.appendChild(noGpuText);
                        gpusContainer.appendChild(noGpuCard);
                    } else {
                        gpusToProcess.forEach((g, i) => {
                            const gid = String(safeVal(g.id, "gpu_"+i));
                            const gc = createEl('div', 'card');
                            gc.style.marginBottom = '16px';
                            gc.id = 'gpu-card-' + gid;
                            
                            const gt = createEl('div', '', g.nome || 'GPU');
                            gt.style.color = 'var(--cor-primaria)';
                            gt.style.fontWeight = '600';
                            gt.style.marginBottom = '12px';
                            gc.appendChild(gt);
                            
                            const gu = createEl('div');
                            gu.id = 'gpu-uso-' + gid;
                            gu.style.fontSize = '36px';
                            gu.style.fontWeight = '700';
                            gc.appendChild(gu);
                            
                            const gb = createEl('div', 'barra-progresso');
                            gb.style.margin = '8px 0';
                            const gbf = createEl('div', 'preenchimento');
                            gbf.id = 'gpu-bar-' + gid;
                            gbf.style.width = '0%';
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
                            const gmtv = createEl('div', 'valor');
                            gmtv.id = 'gpu-temp-' + gid;
                            gmtv.style.fontSize = '20px';
                            gmt.appendChild(gmtv);
                            gm.appendChild(gmt);
                            
                            const gmv = createEl('div', 'card-metrica');
                            gmv.style.padding = '12px';
                            gmv.appendChild(createEl('div', 'rotulo', 'VRAM'));
                            const gmvv = createEl('div', 'valor');
                            gmvv.id = 'gpu-vram-' + gid;
                            gmvv.style.fontSize = '16px';
                            gmv.appendChild(gmvv);
                            gm.appendChild(gmv);
                            
                            gc.appendChild(gm);
                            gpusContainer.appendChild(gc);
                        });
                    }
                }
                
                // Update
                gpusToProcess.forEach((g, i) => {
                    const gid = String(safeVal(g.id, "gpu_"+i));
                    
                    const gu = document.getElementById('gpu-uso-' + gid);
                    const gbf = document.getElementById('gpu-bar-' + gid);
                    const gmtv = document.getElementById('gpu-temp-' + gid);
                    const gmvv = document.getElementById('gpu-vram-' + gid);
                    
                    if (gu) {
                        const valPct = safePct(g.uso_percentual);
                        gu.textContent = valPct;
                        if (valPct !== "N/A") {
                            const guu = createEl('span', '', '%');
                            guu.style.fontSize = '16px';
                            gu.appendChild(guu);
                            if (gbf) {
                                gbf.style.width = valPct + '%';
                                gbf.className = 'preenchimento ' + Phoenix.ui.corPorPercentual(valPct);
                            }
                        } else if (gbf) {
                            gbf.style.width = '0%';
                        }
                    }
                    
                    if (gmtv) {
                        let tempTxt = 'N/A';
                        let corTemp = '';
                        let tempVal = safeVal(g.temperatura_c);
                        if (tempVal !== "N/A" && tempVal >= 0) {
                            tempTxt = tempVal + '°C';
                            corTemp = tempVal >= 85 ? 'var(--cor-erro)' : tempVal >= 70 ? 'var(--cor-alerta)' : 'var(--cor-sucesso)';
                        }
                        gmtv.textContent = tempTxt;
                        if (corTemp) gmtv.style.color = corTemp;
                    }
                    
                    if (gmvv) {
                        let vu = safeVal(g.vram_usada_mb);
                        let vt = safeVal(g.vram_total_mb);
                        if (vu === "N/A" || vt === "N/A") {
                            gmvv.textContent = "N/A";
                        } else {
                            gmvv.textContent = `${vu} / ${vt} MB`;
                        }
                    }
                });
            }

        } catch (e) {
            console.error("Erro no hwmonitor:", e);
        } finally {
            atualizando = false;
        }
    };

    page.leave = function () {
        Phoenix.lifecycle.clearInterval("sensores");
        _reqId++; // invalidate any pending fetch
        atualizando = false;
    };

    page.isUpdatingForTests = () => atualizando;

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.hwmonitor = page;

})(window.Phoenix);
