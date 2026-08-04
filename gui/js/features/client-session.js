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
        
        if (!lista) return;
        while (lista.firstChild) { lista.removeChild(lista.firstChild); }
        
        if (res.clientes && res.clientes.length > 0) {
            const title = document.createElement('div');
            title.style.fontSize = '13px';
            title.style.color = 'var(--cor-texto-secundario)';
            title.style.marginBottom = '10px';
            title.textContent = 'Clientes anteriores:';
            lista.appendChild(title);
            
            res.clientes.forEach(c => {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.cursor = 'pointer';
                card.style.marginBottom = '8px';
                card.style.display = 'flex';
                card.style.alignItems = 'center';
                card.style.gap = '16px';
                card.style.transition = 'border-color 0.15s';
                
                card.addEventListener('mouseover', () => card.style.borderColor = 'var(--cor-primaria)');
                card.addEventListener('mouseout', () => card.style.borderColor = '');
                card.addEventListener('click', () => feature.selectClient(c.id));
                
                const iconDiv = document.createElement('div');
                iconDiv.style.fontSize = '28px';
                iconDiv.textContent = '';
                card.appendChild(iconDiv);
                
                const contentDiv = document.createElement('div');
                contentDiv.style.flex = '1';
                
                const nameDiv = document.createElement('div');
                nameDiv.style.fontWeight = '600';
                nameDiv.textContent = c.nome;
                contentDiv.appendChild(nameDiv);
                
                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'texto-secundario';
                detailsDiv.textContent = `${c.total_atendimentos} atendimento(s) · Último: ${c.ultimo_atendimento || 'Nunca'}`;
                contentDiv.appendChild(detailsDiv);
                
                card.appendChild(contentDiv);
                
                const removeBtn = document.createElement('button');
                removeBtn.style.background = 'transparent';
                removeBtn.style.border = 'none';
                removeBtn.style.color = 'var(--cor-texto-secundario)';
                removeBtn.style.cursor = 'pointer';
                removeBtn.style.fontSize = '16px';
                removeBtn.style.padding = '8px';
                removeBtn.title = 'Remover perfil';
                
                removeBtn.addEventListener('mouseover', () => removeBtn.style.color = 'var(--cor-erro)');
                removeBtn.addEventListener('mouseout', () => removeBtn.style.color = 'var(--cor-texto-secundario)');
                removeBtn.addEventListener('click', (event) => {
                    event.stopPropagation();
                    feature.removeClient(c.id, c.nome);
                });
                removeBtn.textContent = '';
                card.appendChild(removeBtn);
                
                const arrowDiv = document.createElement('div');
                arrowDiv.style.color = 'var(--cor-primaria)';
                arrowDiv.textContent = '→';
                card.appendChild(arrowDiv);
                
                lista.appendChild(card);
            });
        }
    }

    feature.selectClient = async function (id) {
        const res = await bridge.call("selecionar_cliente", id);
        if (res.ok && res.cliente) {
            const tela = document.getElementById('tela-selecao-cliente');
            if (tela) tela.style.display = 'none';
            
            const versaoEl = document.querySelector('.sidebar .versao');
            if (versaoEl) versaoEl.textContent = `v2.0 · ${res.cliente.nome}`;
        }
    };

    feature.removeClient = async function (id, nome) {
        const confirm = await feedback.confirmarModal(
            "Remover Cliente",
            `Deseja realmente apagar o histórico de "${nome}"?`,
            ""
        );
        if (!confirm) return;
        
        const res = await bridge.call("remover_cliente_portable", id);
        if (res.ok) {
            await exibirSelecaoCliente();
        } else {
            console.error("Erro ao remover:", res.erro);
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
        const res = await bridge.call("criar_cliente_portable", nome);
        if (res.ok && res.cliente) {
            await feature.selectClient(res.cliente.id);
        }
    };

    feature.initialize = async function () {
        try {
            const inputNovo = document.getElementById('input-novo-cliente');
            if (inputNovo) {
                inputNovo.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter') {
                        feature.confirmNewClient();
                    }
                });
            }
            const btnNovo = document.getElementById('btn-novo-cliente');
            if (btnNovo) {
                btnNovo.addEventListener('click', feature.confirmNewClient);
            }

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

})(window.Phoenix);
