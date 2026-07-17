(function (Phoenix) {
    "use strict";

    const page = {};

    page.load = async function () {
        await carregarHardware();
    };

    async function carregarHardware() {
        // Registrar abas internas (somente se ainda não registrados, pra evitar duplicação)
        // Usaremos uma delegação no container ou um atributo de flag
        var container = document.getElementById('hw-conteudo');
        if (container && !container.dataset.eventosRegistrados) {
            document.querySelectorAll('.hw-aba').forEach(aba => {
                aba.addEventListener('click', () => {
                    document.querySelectorAll('.hw-aba').forEach(a => a.classList.remove('ativa'));
                    aba.classList.add('ativa');
                    page.renderTab(aba.dataset.aba);
                });
            });
            container.dataset.eventosRegistrados = 'true';
        }
        
        Phoenix.ui.feedback.mostrarOverlay('Coletando informações do sistema...');
        try {
            const res = await Phoenix.bridge.call("obter_info_sistema_detalhado");
            Phoenix.ui.feedback.esconderOverlay();
            if (res && res.ok) {
                Phoenix.state.dadosSistema = res;
                page.renderTab('cpu');
            } else {
                document.getElementById('hw-conteudo').innerHTML = 
                    '<p class="texto-secundario">Erro ao coletar dados.</p>';
            }
        } catch(e) {
            Phoenix.ui.feedback.esconderOverlay();
            document.getElementById('hw-conteudo').innerHTML = 
                '<p class="texto-secundario">Erro ao coletar dados.</p>';
        }
    }

    page.renderTab = function (aba) {
        const d = Phoenix.state.dadosSistema;
        if (!d) return;
        const container = document.getElementById('hw-conteudo');
        
        if (aba === 'cpu') {
            container.innerHTML = `
                <div class="card" style="margin-bottom:16px">
                    <div class="hw-secao-titulo">Processador</div>
                    <table class="tabela-dados">
                        <tr><td>Modelo</td><td>${d.cpu.modelo}</td></tr>
                        <tr><td>Núcleos físicos</td><td>${d.cpu.nucleos_fisicos}</td></tr>
                        <tr><td>Threads lógicas</td><td>${d.cpu.nucleos_logicos}</td></tr>
                        <tr><td>Frequência atual</td><td>${d.cpu.freq_atual ? d.cpu.freq_atual + ' MHz' : 'N/A'}</td></tr>
                        <tr><td>Frequência máxima</td><td>${d.cpu.freq_max ? d.cpu.freq_max + ' MHz' : 'N/A'}</td></tr>
                        <tr><td>Frequência mínima</td><td>${d.cpu.freq_min ? d.cpu.freq_min + ' MHz' : 'N/A'}</td></tr>
                        <tr><td>Arquitetura</td><td>${d.cpu.arquitetura}</td></tr>
                    </table>
                </div>`;
        }
        
        else if (aba === 'gpu') {
            if (!d.gpus || d.gpus.length === 0) {
                container.innerHTML = '<p class="texto-secundario">Nenhuma GPU detectada.</p>';
                return;
            }
            container.innerHTML = d.gpus.map(gpu => `
                <div class="card" style="margin-bottom:16px">
                    <div class="hw-secao-titulo">${gpu.nome}</div>
                    <table class="tabela-dados">
                        <tr><td>Fabricante</td><td>${gpu.fabricante || 'N/A'}</td></tr>
                        <tr><td>VRAM total</td><td>${gpu.vram_total_mb ? (gpu.vram_total_mb/1024).toFixed(1) + ' GB (' + gpu.vram_total_mb + ' MB)' : 'N/A'}</td></tr>
                        <tr><td>VRAM em uso</td><td>${gpu.vram_usada_mb ? gpu.vram_usada_mb + ' MB' : 'N/A'}</td></tr>
                        <tr><td>Uso atual</td><td>${gpu.uso_percentual != null ? gpu.uso_percentual + '%' : 'N/A'}</td></tr>
                        <tr><td>Temperatura</td><td>${gpu.temperatura_c != null ? gpu.temperatura_c + '°C' : 'N/A'}</td></tr>
                        <tr><td>Driver</td><td>${gpu.driver_versao || 'N/A'}</td></tr>
                        <tr><td>Fonte dos dados</td><td>${gpu.fonte_dados || 'N/A'}</td></tr>
                    </table>
                </div>`).join('');
        }
        
        else if (aba === 'memoria') {
            container.innerHTML = `
                <div class="card" style="margin-bottom:16px">
                    <div class="hw-secao-titulo">Memória RAM</div>
                    <table class="tabela-dados">
                        <tr><td>Total instalada</td><td>${d.ram.total_gb} GB</td></tr>
                        <tr><td>Em uso</td><td>${d.ram.usada_gb} GB (${d.ram.percentual}%)</td></tr>
                        <tr><td>Disponível</td><td>${d.ram.disponivel_gb} GB</td></tr>
                    </table>
                    <div class="barra-progresso" style="margin-top:16px">
                        <div class="preenchimento ${d.ram.percentual > 90 ? 'erro' : d.ram.percentual > 70 ? 'alerta' : ''}" 
                            style="width:${d.ram.percentual}%"></div>
                    </div>
                    <div class="texto-secundario" style="margin-top:6px">${d.ram.percentual}% em uso</div>
                </div>`;
        }
        
        else if (aba === 'sistema') {
            container.innerHTML = `
                <div class="card" style="margin-bottom:16px">
                    <div class="hw-secao-titulo">Sistema Operacional</div>
                    <table class="tabela-dados">
                        <tr><td>Sistema</td><td>${d.sistema.os}</td></tr>
                        <tr><td>Versão</td><td>${d.sistema.versao}</td></tr>
                        <tr><td>Arquitetura</td><td>${d.sistema.arquitetura}</td></tr>
                        <tr><td>Tempo ligado</td><td>${d.sistema.uptime}</td></tr>
                    </table>
                </div>`;
        }
        
        else if (aba === 'discos') {
            container.innerHTML = d.discos.map(disco => `
                <div class="card" style="margin-bottom:16px">
                    <div class="hw-secao-titulo">${disco.unidade}</div>
                    <table class="tabela-dados">
                        <tr><td>Total</td><td>${disco.total_gb} GB</td></tr>
                        <tr><td>Usado</td><td>${disco.usado_gb} GB</td></tr>
                        <tr><td>Livre</td><td>${disco.livre_gb} GB</td></tr>
                        <tr><td>Sistema de arquivos</td><td>${disco.fstype}</td></tr>
                    </table>
                    <div class="barra-progresso" style="margin-top:12px">
                        <div class="preenchimento ${disco.percentual > 90 ? 'erro' : disco.percentual > 70 ? 'alerta' : ''}"
                            style="width:${disco.percentual}%"></div>
                    </div>
                    <div class="texto-secundario" style="margin-top:6px">${disco.percentual}% ocupado</div>
                </div>`).join('');
        }
    };

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.hardware = page;

    // Globais para compatibilidade temporária de manipulação de HTML inline (onclicks)
    window.renderizarAbaHardware = function (aba) {
        document.querySelectorAll('.hw-aba').forEach(a => a.classList.remove('ativa'));
        var el = document.querySelector('.hw-aba[data-aba="' + aba + '"]');
        if (el) el.classList.add('ativa');
        page.renderTab(aba);
    };

})(window.Phoenix);
