(function (Phoenix) {
    "use strict";

    const page = {};

    page.load = async function () {
        await carregarDiagnostico();
    };

    async function carregarDiagnostico() {
        Phoenix.ui.feedback.mostrarOverlay("Coletando diagnóstico...");
        try {
            var jobRes = await Phoenix.bridge.call("obter_diagnostico");
            if (!jobRes || !jobRes.job_id) {
                Phoenix.ui.feedback.esconderOverlay();
                return;
            }
            var resultado = await Phoenix.jobs.awaitJob(jobRes.job_id);
            Phoenix.ui.feedback.esconderOverlay();
            renderizarDiagnostico(resultado);
        } catch (e) {
            console.error("[ERRO] Diagnóstico:", e);
            Phoenix.ui.feedback.esconderOverlay();
        }
    }

    function renderizarDiagnostico(resultado) {
        var container = document.getElementById("conteudo-diagnostico");
        if (!container) return;

        if (!resultado || !resultado.ok) {
            container.innerHTML =
                '<div class="card"><span class="badge erro">Erro</span> ' +
                ((resultado && resultado.erro) || "Erro desconhecido") +
                "</div>";
            return;
        }

        var d = resultado.dados;
        var cpuPct = d.cpu.uso_percentual || 0;
        var ramPct = d.memoria.percentual_uso || 0;
        var discos = d.discos || [];
        var maiorUsoDiscos = 0;
        if (discos.length > 0) {
            maiorUsoDiscos = Math.max.apply(null, discos.map(function(disk) { return disk.percentual_uso || 0; }));
        }

        // Score & Warnings
        var scoreCPU = Math.max(0, 100 - cpuPct);
        var scoreRAM = Math.max(0, 100 - ramPct);
        var scoreDisco = Math.max(0, 100 - maiorUsoDiscos);
        var scoreGeral = Math.round((scoreCPU + scoreRAM + scoreDisco) / 3);

        var problemas = [];
        if (cpuPct > 80) problemas.push("CPU sobrecarregada");
        if (ramPct > 85) problemas.push("Memória no limite");
        if (maiorUsoDiscos > 70) problemas.push("Disco quase cheio");

        var numProblemas = problemas.length;
        var corFundo, corBorda, icone, titulo, subtitulo, corTexto;
        
        if (numProblemas === 0) {
            corFundo = 'rgba(111, 174, 124, 0.1)';
            corBorda = 'rgba(111, 174, 124, 0.2)';
            icone = '✅';
            titulo = 'PC em bom estado — nenhuma ação necessária';
            subtitulo = 'Todos os parâmetros estão dentro da normalidade.';
            corTexto = 'var(--cor-sucesso)';
        } else if (numProblemas === 1 || numProblemas === 2) {
            corFundo = 'rgba(217, 162, 59, 0.1)';
            corBorda = 'rgba(217, 162, 59, 0.2)';
            icone = '⚠️';
            titulo = 'Atenção — ' + numProblemas + ' pontos de melhoria detectados';
            subtitulo = problemas.join(', ') + '.';
            corTexto = 'var(--cor-alerta)';
        } else {
            corFundo = 'rgba(194, 85, 74, 0.1)';
            corBorda = 'rgba(194, 85, 74, 0.2)';
            icone = '🚨';
            titulo = 'PC sobrecarregado — ação recomendada';
            subtitulo = problemas.join(', ') + '.';
            corTexto = 'var(--cor-erro)';
        }

        var bannerHtml = `
            <div style="
                background: linear-gradient(135deg, ${corFundo}, transparent);
                border: 1px solid ${corBorda};
                border-radius: var(--raio-md);
                padding: 20px 24px;
                display: flex;
                align-items: center;
                gap: 16px;
                margin-bottom: 24px;
            ">
                <div style="font-size: 36px">${icone}</div>
                <div>
                    <div style="font-size:18px;font-weight:700;color:${corTexto}">${titulo}</div>
                    <div style="color:var(--cor-texto-secundario);font-size:13px">${subtitulo}</div>
                </div>
                <div style="margin-left:auto;font-size:48px;font-weight:800;
                    color:${corTexto};opacity:0.15">${scoreGeral}</div>
            </div>`;

        function corBadge(pct) { return pct >= 80 ? 'erro' : pct >= 60 ? 'alerta' : 'sucesso'; }
        function textoBadge(pct) { return pct >= 80 ? 'Crítico' : pct >= 60 ? 'Atenção' : 'Ótimo'; }
        function corBarra(pct) { return pct >= 80 ? 'erro' : pct >= 60 ? 'alerta' : ''; }

        var numProc = (d.processos || []).length;
        var cardsHtml = `
            <div class="grade-cards">
                <div class="card-metrica">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="rotulo">CPU</div>
                        <span class="badge ${corBadge(cpuPct)}">${textoBadge(cpuPct)}</span>
                    </div>
                    <div class="valor">${cpuPct}<span class="unidade">%</span></div>
                    <div class="barra-progresso"><div class="preenchimento ${corBarra(cpuPct)}" style="width:${cpuPct}%"></div></div>
                    <div class="texto-secundario mt-0">Uso atual de CPU</div>
                </div>
                
                <div class="card-metrica">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="rotulo">Memória RAM</div>
                        <span class="badge ${corBadge(ramPct)}">${textoBadge(ramPct)}</span>
                    </div>
                    <div class="valor">${ramPct}<span class="unidade">%</span></div>
                    <div class="barra-progresso"><div class="preenchimento ${corBarra(ramPct)}" style="width:${ramPct}%"></div></div>
                    <div class="texto-secundario mt-0">${d.memoria.disponivel_gb} GB disponíveis</div>
                </div>
                
                <div class="card-metrica">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="rotulo">Disco (C:)</div>
                        <span class="badge ${corBadge(maiorUsoDiscos)}">${textoBadge(maiorUsoDiscos)}</span>
                    </div>
                    <div class="valor">${maiorUsoDiscos}<span class="unidade">%</span></div>
                    <div class="barra-progresso"><div class="preenchimento ${corBarra(maiorUsoDiscos)}" style="width:${maiorUsoDiscos}%"></div></div>
                    <div class="texto-secundario mt-0">Uso do disco principal</div>
                </div>

                <div class="card-metrica">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="rotulo">Processos</div>
                        <span class="badge neutro">Info</span>
                    </div>
                    <div class="valor">${numProc}</div>
                    <div class="barra-progresso"><div class="preenchimento" style="width:100%; opacity:0.1"></div></div>
                    <div class="texto-secundario mt-0">Executando no momento</div>
                </div>
            </div>`;

        var processosHtml = '';
        if (cpuPct > 70 || ramPct > 70) {
            var topProcessos = (d.processos || []).slice(0, 5).map(function(p) {
                var cpuP = p.cpu_percent || 0;
                var ramP = p.memory_percent || 0;
                var badgeProc = (cpuP > 20 || ramP > 10) ? 'erro' : (cpuP > 10 || ramP > 5) ? 'alerta' : 'sucesso';
                var textProc = (cpuP > 20 || ramP > 10) ? 'Alto impacto' : (cpuP > 10 || ramP > 5) ? 'Médio impacto' : 'Baixo impacto';
                return '<tr><td>' + (p.name || "desconhecido") + ' <span class="badge ' + badgeProc + '" style="margin-left:8px;font-size:9px">' + textProc + '</span></td>' +
                             '<td>' + cpuP.toFixed(1) + '%</td><td>' + ramP.toFixed(1) + '%</td></tr>';
            }).join('');
            
            processosHtml = `
                <div class="card" id="secao-processos">
                    <strong>Processos com maior consumo</strong>
                    <table class="tabela-dados" style="margin-top:12px">
                        <thead><tr><th>Processo</th><th>CPU</th><th>RAM</th></tr></thead>
                        <tbody>${topProcessos}</tbody>
                    </table>
                </div>`;
        }

        var acoesHtml = '';
        if (maiorUsoDiscos > 70) {
            acoesHtml += `
                <div class="card" style="border-left: 3px solid var(--cor-primaria); display:flex; align-items:center; gap:16px; cursor:pointer" onclick="if(window.irParaPagina) window.irParaPagina('limpeza'); else document.querySelector('.item-menu[data-pagina=\\'limpeza\\']').click()">
                    <div style="font-size:24px">🧹</div>
                    <div style="flex:1">
                        <div style="font-weight:600">Executar limpeza</div>
                        <div class="texto-secundario">O disco está cheio. Remova arquivos temporários e libere espaço.</div>
                    </div>
                    <button class="botao primario" style="flex-shrink:0">Limpar</button>
                </div>`;
        }
        
        if (cpuPct > 80) {
            acoesHtml += `
                <div class="card" style="border-left: 3px solid var(--cor-primaria); display:flex; align-items:center; gap:16px; cursor:pointer" onclick="document.getElementById('secao-processos') && document.getElementById('secao-processos').scrollIntoView({behavior: 'smooth'})">
                    <div style="font-size:24px">⚙️</div>
                    <div style="flex:1">
                        <div style="font-weight:600">Ver processos em segundo plano</div>
                        <div class="texto-secundario">O uso da CPU está elevado. Verifique os processos ativos.</div>
                    </div>
                    <button class="botao primario" style="flex-shrink:0">Ver processos</button>
                </div>`;
        }
        
        if (acoesHtml === '') {
            acoesHtml = `
                <div class="card" style="border-left: 3px solid var(--cor-primaria); display:flex; align-items:center; gap:16px; cursor:pointer" onclick="if(window.irParaPagina) window.irParaPagina('otimizacao'); else document.querySelector('.item-menu[data-pagina=\\'otimizacao\\']').click()">
                    <div style="font-size:24px">⚡</div>
                    <div style="flex:1">
                        <div style="font-weight:600">Aplicar otimizações</div>
                        <div class="texto-secundario">Melhore o desempenho geral com ajustes no sistema.</div>
                    </div>
                    <button class="botao primario" style="flex-shrink:0">Otimizar</button>
                </div>`;
        }
        
        var recomendacoesContainer = `
            <div style="margin-top:24px">
                <h3 style="color:var(--cor-texto);font-size:16px;margin-bottom:12px">Ações recomendadas</h3>
                ${acoesHtml}
            </div>`;

        container.innerHTML = bannerHtml + cardsHtml + processosHtml + recomendacoesContainer;
    }

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.diagnostico = page;
})(window.Phoenix);
