(function (Phoenix) {
    "use strict";

    const page = {};

    function safeText(text) {
        return text != null ? String(text) : "N/A";
    }

    function createEl(tag, className, textContent) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (textContent !== undefined) el.textContent = textContent;
        return el;
    }

    function formatData(isoString) {
        if (!isoString) return "Desconhecida";
        try {
            const date = new Date(isoString);
            return date.toLocaleString('pt-BR');
        } catch {
            return isoString;
        }
    }

    page.load = async function () {
        const btn = document.getElementById('btn-atualizar-hardware');
        if (btn && !btn.dataset.ev) {
            btn.addEventListener('click', async () => {
                btn.disabled = true;
                btn.textContent = "Atualizando...";
                try {
                    const res = await Phoenix.bridge.call("forcar_rescan_hardware");
                    if (!res || !res.job_id) {
                        Phoenix.ui.feedback.mostrarOverlay("Falha ao iniciar", true);
                        Phoenix.ui.feedback.esconderOverlay(true, false);
                        return;
                    }

                    Phoenix.ui.feedback.mostrarOverlay("Atualizando inventário", true);
                    const jobResult = await Phoenix.jobs.awaitJob(res.job_id, (pct, msg) => {
                        Phoenix.ui.feedback.atualizarOverlay(msg, pct);
                    });

                    if (jobResult && jobResult.ok) {
                        Phoenix.state.hardware = jobResult.hardware || Phoenix.state.hardware;
                        await carregarHardware();
                        if (Phoenix.ui && Phoenix.ui.visualEffects && typeof Phoenix.ui.visualEffects.refresh === 'function') {
                            Phoenix.ui.visualEffects.refresh();
                        }

                        const hwStatus = jobResult.hardware && jobResult.hardware.status;
                        if (hwStatus === "parcial") {
                            Phoenix.ui.feedback.atualizarOverlay("Atualizado parcialmente.", 100);
                        }
                        Phoenix.ui.feedback.esconderOverlay(true, true);
                    } else {
                        const msgErro = jobResult && jobResult.erro ? jobResult.erro : "Não foi possível concluir a varredura.";
                        Phoenix.ui.feedback.atualizarOverlay(msgErro);
                        Phoenix.ui.feedback.esconderOverlay(true, false);
                    }
                } catch(e) {
                    Phoenix.ui.feedback.mostrarOverlay("Erro interno", true);
                    Phoenix.ui.feedback.esconderOverlay(true, false);
                } finally {
                    btn.disabled = false;
                    btn.textContent = "Atualizar inventário";
                }
            });
            btn.dataset.ev = "1";
        }
        await carregarHardware();
    };

    async function carregarHardware() {
        const container = document.getElementById('hw-conteudo');
        while (container.firstChild) { container.removeChild(container.firstChild); } // safe clear
        
        const badge = document.getElementById('hw-status-badge');
        const dataLbl = document.getElementById('hw-data-coleta');

        try {
            const hw = await Phoenix.bridge.call("obter_inventario_atual");
            
            if (!hw || !hw.sistema) {
                container.appendChild(createEl('p', 'texto-secundario', 'Inventário não disponível. Tente atualizar.'));
                badge.textContent = "Não carregado";
                badge.style.background = "#555";
                dataLbl.textContent = "";
                return;
            }

            // Atualiza cabeçalho
            if (hw.status === 'completo') {
                badge.textContent = "Completo";
                badge.style.background = "var(--cor-sucesso, #2e7d32)";
            } else if (hw.status === 'parcial') {
                badge.textContent = "Parcial";
                badge.style.background = "var(--cor-alerta, #f57c00)";
            } else {
                badge.textContent = "Falha";
                badge.style.background = "var(--cor-erro, #d32f2f)";
            }
            dataLbl.textContent = "Atualizado em: " + formatData(hw.coletado_em);

            renderizarResumo(hw, container);
            renderizarSistema(hw, container);
            renderizarCPU(hw, container);
            renderizarMemoria(hw, container);
            renderizarGPUs(hw, container);
            renderizarArmazenamento(hw, container);

        } catch(e) {
            container.appendChild(createEl('p', 'texto-secundario', 'Erro ao carregar inventário.'));
            console.error(e);
        }
    }

    function renderizarResumo(hw, container) {
        const grid = createEl('div', 'grade-cards');
        grid.style.marginBottom = '24px';
        
        const sysCard = createEl('div', 'card');
        sysCard.appendChild(createEl('div', 'hw-secao-titulo', 'Sistema'));
        sysCard.appendChild(createEl('div', '', hw.sistema.modelo || hw.sistema.placa_mae.modelo || 'Computador genérico'));
        sysCard.appendChild(createEl('div', 'texto-secundario', `${hw.sistema.os_nome} · Build ${safeText(hw.sistema.os_build)}`));
        grid.appendChild(sysCard);

        const cpuCard = createEl('div', 'card');
        cpuCard.appendChild(createEl('div', 'hw-secao-titulo', 'Processador'));
        cpuCard.appendChild(createEl('div', '', safeText(hw.cpu.modelo)));
        cpuCard.appendChild(createEl('div', 'texto-secundario', `${safeText(hw.cpu.nucleos_fisicos)} núcleos / ${safeText(hw.cpu.threads_logicas)} threads`));
        grid.appendChild(cpuCard);

        const ramCard = createEl('div', 'card');
        ramCard.appendChild(createEl('div', 'hw-secao-titulo', 'Memória'));
        ramCard.appendChild(createEl('div', '', `${safeText(hw.memoria.total_instalada_gb)} GB RAM`));
        const slotsText = hw.memoria.slots_usados != null ? `${hw.memoria.slots_usados} módulo(s)` : '';
        ramCard.appendChild(createEl('div', 'texto-secundario', slotsText));
        grid.appendChild(ramCard);

        if (hw.gpus && hw.gpus.length > 0) {
            const gpuCard = createEl('div', 'card');
            gpuCard.appendChild(createEl('div', 'hw-secao-titulo', 'GPU Principal'));
            gpuCard.appendChild(createEl('div', '', hw.gpus[0].nome));
            const tipoText = hw.gpus[0].tipo === 'dedicada' ? 'Dedicada' : (hw.gpus[0].tipo === 'integrada' ? 'Integrada' : 'Desconhecida');
            gpuCard.appendChild(createEl('div', 'texto-secundario', tipoText));
            grid.appendChild(gpuCard);
        }

        container.appendChild(grid);
    }

    function createList(dataObj) {
        const wrapper = createEl('div', 'hw-lista-dados');
        for (const [key, val] of Object.entries(dataObj)) {
            const row = createEl('div', 'hw-lista-item');
            const lbl = createEl('div', 'hw-lista-rotulo', key);
            const valEl = createEl('div', 'hw-lista-valor', val);
            row.appendChild(lbl);
            row.appendChild(valEl);
            wrapper.appendChild(row);
        }
        return wrapper;
    }

    function renderizarSistema(hw, container) {
        const card = createEl('div', 'card');
        card.style.marginBottom = '16px';
        card.appendChild(createEl('div', 'hw-secao-titulo', 'Detalhes do Sistema'));
        
        card.appendChild(createList({
            "Fabricante": safeText(hw.sistema.fabricante),
            "Modelo": safeText(hw.sistema.modelo),
            "Dispositivo": safeText(hw.sistema.nome_dispositivo),
            "SO": safeText(hw.sistema.os_nome),
            "Build": safeText(hw.sistema.os_build),
            "Arquitetura": safeText(hw.sistema.arquitetura),
            "Placa-mãe": safeText(hw.sistema.placa_mae.modelo),
            "Fabricante Placa-mãe": safeText(hw.sistema.placa_mae.fabricante),
            "Versão BIOS": safeText(hw.sistema.bios.versao),
            "Data BIOS": safeText(hw.sistema.bios.data)
        }));
        
        container.appendChild(card);
    }

    function renderizarCPU(hw, container) {
        const card = createEl('div', 'card');
        card.style.marginBottom = '16px';
        card.appendChild(createEl('div', 'hw-secao-titulo', 'Processador (CPU)'));
        
        card.appendChild(createList({
            "Nome": safeText(hw.cpu.modelo),
            "Fabricante": safeText(hw.cpu.fabricante),
            "Arquitetura": safeText(hw.cpu.arquitetura),
            "Núcleos Físicos": safeText(hw.cpu.nucleos_fisicos),
            "Threads Lógicas": safeText(hw.cpu.threads_logicas),
            "Frequência Máxima": hw.cpu.frequencia_max_mhz ? hw.cpu.frequencia_max_mhz + " MHz" : "N/A"
        }));
        container.appendChild(card);
    }

    function renderizarMemoria(hw, container) {
        const card = createEl('div', 'card');
        card.style.marginBottom = '16px';
        card.appendChild(createEl('div', 'hw-secao-titulo', 'Memória RAM'));
        
        card.appendChild(createList({
            "Total Instalada": safeText(hw.memoria.total_instalada_gb) + " GB",
            "Total Utilizável": safeText(hw.memoria.total_utilizavel_gb) + " GB",
            "Slots Usados": safeText(hw.memoria.slots_usados)
        }));
        
        if (hw.memoria.modulos && hw.memoria.modulos.length > 0) {
            const ul = createEl('ul');
            ul.style.listStyleType = 'none';
            ul.style.padding = '0';
            ul.style.marginTop = '12px';
            
            hw.memoria.modulos.forEach(m => {
                const li = createEl('li');
                li.style.background = 'rgba(255,255,255,0.03)';
                li.style.padding = '8px 12px';
                li.style.borderRadius = '4px';
                li.style.marginBottom = '8px';
                
                const title = createEl('div', '', m.slot ? m.slot : "Módulo");
                title.style.fontWeight = 'bold';
                li.appendChild(title);
                
                let details = `${safeText(m.capacidade_gb)} GB`;
                if (m.velocidade_mhz) details += ` · ${m.velocidade_mhz} MHz`;
                if (m.fabricante) details += ` · ${m.fabricante}`;
                if (m.part_number) details += ` (PN: ${m.part_number})`;
                
                const desc = createEl('div', 'texto-secundario', details);
                desc.style.fontSize = '13px';
                li.appendChild(desc);
                ul.appendChild(li);
            });
            card.appendChild(ul);
        }
        
        container.appendChild(card);
    }

    function renderizarGPUs(hw, container) {
        if (!hw.gpus || hw.gpus.length === 0) {
            const card = createEl('div', 'card');
            card.style.marginBottom = '16px';
            card.appendChild(createEl('div', 'hw-secao-titulo', 'Adaptadores de Vídeo (GPU)'));
            card.appendChild(createEl('div', 'badge', 'Não detectado'));
            container.appendChild(card);
            return;
        }

        hw.gpus.forEach((gpu, index) => {
            const card = createEl('div', 'card');
            card.style.marginBottom = '16px';
            
            const titleRow = createEl('div');
            titleRow.style.display = 'flex';
            titleRow.style.justifyContent = 'space-between';
            titleRow.style.alignItems = 'center';
            titleRow.style.marginBottom = '12px';
            
            const title = createEl('div', 'hw-secao-titulo', gpu.nome || `GPU ${index+1}`);
            title.style.margin = '0';
            titleRow.appendChild(title);
            
            let tipoColor = "#555";
            if (gpu.tipo === 'dedicada') tipoColor = "var(--cor-primaria)";
            if (gpu.tipo === 'integrada') tipoColor = "var(--cor-painel-borda)";
            
            const tipoBadge = createEl('span', 'badge', gpu.tipo.toUpperCase());
            tipoBadge.style.background = tipoColor;
            tipoBadge.style.padding = '4px 8px';
            tipoBadge.style.borderRadius = '4px';
            tipoBadge.style.fontSize = '11px';
            titleRow.appendChild(tipoBadge);
            
            card.appendChild(titleRow);
            
            let vramText = "N/A";
            if (gpu.vram_status === "exata" && gpu.vram_total_mb != null) {
                vramText = `${gpu.vram_total_mb} MB (${(gpu.vram_total_mb/1024).toFixed(1)} GB)`;
            } else if (gpu.vram_status === "estimada") {
                vramText = `Capacidade não confirmada`;
            } else if (gpu.vram_status === "compartilhada") {
                vramText = `Memória compartilhada`;
            } else if (gpu.vram_status === "indisponivel") {
                vramText = `Indisponível`;
            } else if (gpu.vram_total_mb) {
                vramText = `${gpu.vram_total_mb} MB (${(gpu.vram_total_mb/1024).toFixed(1)} GB)`;
            } else {
                vramText = "Indisponível";
            }
            
            card.appendChild(createList({
                "Fabricante": safeText(gpu.fabricante),
                "VRAM": vramText,
                "Driver Versão": safeText(gpu.driver_versao),
                "Driver Data": safeText(gpu.driver_data),
            }));
            
            container.appendChild(card);
        });
    }

    function renderizarArmazenamento(hw, container) {
        // Discos Físicos
        const dCard = createEl('div', 'card');
        dCard.style.marginBottom = '16px';
        dCard.appendChild(createEl('div', 'hw-secao-titulo', 'Discos Físicos'));
        
        if (!hw.armazenamento.discos_fisicos || hw.armazenamento.discos_fisicos.length === 0) {
            dCard.appendChild(createEl('p', 'texto-secundario', 'Nenhum disco detectado.'));
        } else {
            hw.armazenamento.discos_fisicos.forEach(d => {
                const inner = createEl('div');
                inner.style.background = 'rgba(255,255,255,0.02)';
                inner.style.padding = '12px';
                inner.style.borderRadius = '6px';
                inner.style.marginBottom = '8px';
                
                const title = createEl('div', '', safeText(d.modelo));
                title.style.fontWeight = 'bold';
                title.style.marginBottom = '6px';
                inner.appendChild(title);
                
                inner.appendChild(createList({
                    "Tipo": safeText(d.tipo_midia),
                    "Barramento": safeText(d.barramento),
                    "Capacidade": d.capacidade_gb ? d.capacidade_gb + " GB" : "N/A",
                    "Saúde": safeText(d.saude)
                }));
                dCard.appendChild(inner);
            });
        }
        container.appendChild(dCard);

        // Volumes
        const vCard = createEl('div', 'card');
        vCard.style.marginBottom = '16px';
        vCard.appendChild(createEl('div', 'hw-secao-titulo', 'Volumes'));
        
        if (!hw.armazenamento.volumes || hw.armazenamento.volumes.length === 0) {
            vCard.appendChild(createEl('p', 'texto-secundario', 'Nenhum volume detectado.'));
        } else {
            hw.armazenamento.volumes.forEach(v => {
                const inner = createEl('div');
                inner.style.background = 'rgba(255,255,255,0.02)';
                inner.style.padding = '12px';
                inner.style.borderRadius = '6px';
                inner.style.marginBottom = '8px';
                
                const header = createEl('div');
                header.style.display = 'flex';
                header.style.justifyContent = 'space-between';
                header.style.fontWeight = 'bold';
                header.style.marginBottom = '8px';
                
                const nm = v.rotulo ? `${v.unidade} (${v.rotulo})` : v.unidade;
                header.appendChild(createEl('span', '', nm));
                
                if (v.tipo) {
                    const badge = createEl('span', 'badge', v.tipo.toUpperCase());
                    badge.style.background = '#444';
                    badge.style.padding = '3px 6px';
                    badge.style.borderRadius = '4px';
                    badge.style.fontSize = '10px';
                    header.appendChild(badge);
                }
                inner.appendChild(header);
                
                inner.appendChild(createList({
                    "Sistema de Arquivos": safeText(v.sistema_arquivos),
                    "Capacidade": v.total_gb ? v.total_gb + " GB" : "N/A",
                    "Livre": v.livre_gb ? v.livre_gb + " GB" : "N/A"
                }));
                
                if (v.percentual_uso != null) {
                    const barContainer = createEl('div', 'barra-progresso');
                    barContainer.style.marginTop = '12px';
                    
                    const fill = createEl('div', 'preenchimento');
                    if (v.percentual_uso > 90) fill.classList.add('erro');
                    else if (v.percentual_uso > 75) fill.classList.add('alerta');
                    
                    fill.style.width = v.percentual_uso + '%';
                    barContainer.appendChild(fill);
                    inner.appendChild(barContainer);
                    
                    const pctText = createEl('div', 'texto-secundario', v.percentual_uso + '% ocupado');
                    pctText.style.marginTop = '6px';
                    pctText.style.fontSize = '12px';
                    inner.appendChild(pctText);
                }
                
                vCard.appendChild(inner);
            });
        }
        container.appendChild(vCard);
    }

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.hardware = page;

})(window.Phoenix);
