(function (Phoenix) {
    "use strict";

    const bridge = Phoenix.bridge;
    const feedback = Phoenix.ui.feedback;

    const feature = {};

    async function exibirSelecaoCliente() {
        const tela = document.getElementById('tela-selecao-cliente');
        if (tela) tela.style.display = 'flex';
        
        const res = await bridge.call("obter_clientes_portable");
        const lista = document.getElementById('lista-clientes-portable');
        
        if (res.clientes && res.clientes.length > 0) {
            lista.innerHTML = `
                <div style="font-size:13px;color:var(--cor-texto-secundario);
                    margin-bottom:10px">Clientes anteriores:</div>
                ${res.clientes.map(c => `
                    <div class="card" style="cursor:pointer;margin-bottom:8px;
                        display:flex;align-items:center;gap:16px;
                        transition:border-color 0.15s"
                        onmouseover="this.style.borderColor='var(--cor-primaria)'"
                        onmouseout="this.style.borderColor=''"
                        onclick="selecionarCliente('${c.nome.replace(/'/g, "\\'")}')">
                        <div style="font-size:28px">👤</div>
                        <div style="flex:1">
                            <div style="font-weight:600">${c.nome}</div>
                            <div class="texto-secundario">
                                ${c.total_atendimentos} atendimento(s) · 
                                Último: ${c.ultimo_atendimento || 'Nunca'}
                            </div>
                        </div>
                        <button style="background:transparent;border:none;color:var(--cor-texto-secundario);
                            cursor:pointer;font-size:16px;padding:8px" 
                            title="Remover perfil"
                            onmouseover="this.style.color='var(--cor-erro)'"
                            onmouseout="this.style.color='var(--cor-texto-secundario)'"
                            onclick="event.stopPropagation(); removerCliente('${c.id.replace(/'/g, "\\'")}', '${c.nome.replace(/'/g, "\\'")}')">
                            🗑️
                        </button>
                        <div style="color:var(--cor-primaria)">→</div>
                    </div>
                `).join('')}
            `;
        } else {
            lista.innerHTML = '';
        }
    }

    feature.selectClient = async function (nome) {
        const res = await bridge.call("selecionar_cliente", nome);
        if (res.ok) {
            const tela = document.getElementById('tela-selecao-cliente');
            if (tela) tela.style.display = 'none';
            
            const versaoEl = document.querySelector('.sidebar .versao');
            if (versaoEl) versaoEl.textContent = `v2.0 · ${nome}`;
        }
    };

    feature.removeClient = async function (id, nome) {
        const confirm = await feedback.confirmarModal(
            "Remover Cliente",
            `Deseja realmente apagar o histórico de "${nome}"?`,
            "🗑️"
        );
        if (!confirm) return;
        
        const res = await bridge.call("remover_cliente_portable", id);
        if (res.ok) {
            await exibirSelecaoCliente();
        }
    };

    feature.confirmNewClient = async function () {
        const input = document.getElementById('input-novo-cliente');
        const nome = input?.value?.trim();
        if (!nome) {
            if (input) {
                input.style.borderColor = 'var(--cor-erro)';
                setTimeout(() => input.style.borderColor = '', 1500);
            }
            return;
        }
        await feature.selectClient(nome);
    };

    feature.initialize = async function () {
        try {
            const modoRes = await bridge.call("obter_modo_portable");
            if (modoRes.portable) {
                await exibirSelecaoCliente();
            }
        } catch(e) {
            console.error("[ERRO] clientSession.initialize:", e);
        }
    };

    Phoenix.features = Phoenix.features || {};
    Phoenix.features.clientSession = feature;

    // Manter aliases de compatibilidade no window para os eventos onclick (HTML)
    window.selecionarCliente = feature.selectClient;
    window.removerCliente = feature.removeClient;
    window.confirmarNovoCliente = feature.confirmNewClient;

})(window.Phoenix);
