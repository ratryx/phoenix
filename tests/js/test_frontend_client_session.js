const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'features', 'client-session.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: { setTimeout: (fn, ms) => fn() },
        setTimeout: setTimeout,
        clearTimeout: clearTimeout,
        document: {
            createElement: function(tag) {
                return {
                    tagName: tag,
                    style: {},
                    className: '',
                    children: [],
              removeChild: function(c) { if (!this.children) return;
                const i = this.children.indexOf(c);
                if (i !== -1) this.children.splice(i, 1);
              },
              get firstChild() { return (this.children && this.children.length > 0) ? this.children[0] : null; },
                    appendChild: function(child) { this.children.push(child); },
                    addEventListener: function(evt, cb) { 
                        this.listeners = this.listeners || {};
                        this.listeners[evt] = cb; 
                    }
                };
            },
            getElementById: function(id) {
                if (id === 'tela-selecao-cliente') return context.dom.telaSelecao;
                if (id === 'lista-clientes-portable') return context.dom.listaClientes;
                if (id === 'input-novo-cliente') return context.dom.inputNovo;
                return null;
            },
            querySelector: function(sel) {
                if (sel === '.sidebar .versao') return context.dom.versaoEl;
                return null;
            }
        },
        console: {
            error: function () { context.errors.push(Array.from(arguments)); },
            log: function () { context.logs.push(Array.from(arguments)); }
        },
        Phoenix: {
            bridge: {
                call: async function(endpoint, args) {
                    context.metrics.endpointsCalled.push({endpoint, args});
                    if (context.mocks.bridgeReject) throw new Error("Bridge reject");
                    
                    if (endpoint === "obter_modo_portable") {
                        return { portable: context.mocks.isPortable };
                    }
                    if (endpoint === "obter_clientes_portable") {
                        return { clientes: context.mocks.clientesList };
                    }
                    if (endpoint === "selecionar_cliente") {
                        return { ok: !context.mocks.selecaoFails, cliente: { id: args, nome: "Nome " + args } };
                    }
                    if (endpoint === "remover_cliente_portable") {
                        return { ok: !context.mocks.remocaoFails };
                    }
                    if (endpoint === "criar_cliente_portable") {
                        return { ok: true, cliente: { id: "novo-" + args, nome: args } };
                    }
                    return {};
                }
            },
            ui: {
                feedback: {
                    confirmarModal: async function(titulo, msg, icone) {
                        context.metrics.modalShownCount++;
                        return !context.mocks.cancelModal;
                    }
                }
            }
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.errors = [];
    context.logs = [];
    
    context.dom = {
        telaSelecao: { style: { display: 'none' } },
        listaClientes: { 
            innerHTML: '', 
            children: [],
              removeChild: function(c) { if (!this.children) return;
                const i = this.children.indexOf(c);
                if (i !== -1) this.children.splice(i, 1);
              },
              get firstChild() { return (this.children && this.children.length > 0) ? this.children[0] : null; },
            appendChild: function(child) { this.children.push(child); }
        },
        inputNovo: { 
            value: '', 
            style: { borderColor: '' },
            addEventListener: function(evt, cb) { 
                this.listeners = this.listeners || {};
                this.listeners[evt] = cb; 
            }
        },
        versaoEl: { textContent: 'v2.0' }
    };

    context.metrics = {
        endpointsCalled: [],
        modalShownCount: 0
    };
    
    context.mocks = {
        bridgeReject: false,
        isPortable: true,
        clientesList: [],
        selecaoFails: false,
        remocaoFails: false,
        cancelModal: false
    };

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes Client Session...");

    // Teste 1: Registro
    {
        const ctx = setupEnvironment();
        assert.ok(ctx.Phoenix.features.clientSession, "Namespace deve existir");
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 0, "Nenhum endpoint ao importar");
    }

    // Teste 2: Inicialização em modo Portable com lista vazia
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.features.clientSession.initialize();
        assert.strictEqual(ctx.dom.telaSelecao.style.display, 'flex', "Deve mostrar tela de seleção");
        assert.strictEqual(ctx.dom.listaClientes.children.length, 0, "Deve ter lista vazia");
    }

    // Teste 3: Inicialização em modo Não Portable
    {
        const ctx = setupEnvironment();
        ctx.mocks.isPortable = false;
        await ctx.Phoenix.features.clientSession.initialize();
        assert.strictEqual(ctx.dom.telaSelecao.style.display, 'none', "Não deve exibir tela se não for portable");
    }

    // Teste 4: Inicialização com clientes em modo Portable
    {
        const ctx = setupEnvironment();
        ctx.mocks.clientesList = [
            { id: "1", nome: "Empresa <script>A</script>", total_atendimentos: 5, ultimo_atendimento: "2026-07-16" }
        ];
        await ctx.Phoenix.features.clientSession.initialize();
        assert.ok(ctx.dom.listaClientes.children.length > 0, "Lista de clientes deve renderizar 'Empresa A'");
        const title = ctx.dom.listaClientes.children[0];
        const card = ctx.dom.listaClientes.children[1];
        const textNodes = card.children.find(c => c.style.flex === '1');
        const nameNode = textNodes.children[0];
        assert.strictEqual(nameNode.textContent, "Empresa <script>A</script>", "Deve usar textContent mitigando XSS");
        assert.ok(typeof card.listeners.click === 'function', "Deve ter event listener de clique");
    }

    // Teste 5: Seleção de cliente
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.features.clientSession.selectClient("id-cliente-z");
        assert.ok(ctx.metrics.endpointsCalled.some(e => e.endpoint === "selecionar_cliente" && e.args === "id-cliente-z"));
        assert.strictEqual(ctx.dom.telaSelecao.style.display, 'none', "Ao selecionar, esconde a tela");
        assert.ok(ctx.dom.versaoEl.textContent.includes("Nome id-cliente-z"), "Atualiza a UI (versaoEl)");
    }

    // Teste 6: Remoção de cliente (confirma)
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.features.clientSession.removeClient("id-123", "Joao");
        assert.strictEqual(ctx.metrics.modalShownCount, 1, "Deve exibir modal");
        assert.ok(ctx.metrics.endpointsCalled.some(e => e.endpoint === "remover_cliente_portable" && e.args === "id-123"), "Deve chamar endpoint");
    }

    // Teste 7: Remoção de cliente (cancela no modal)
    {
        const ctx = setupEnvironment();
        ctx.mocks.cancelModal = true;
        await ctx.Phoenix.features.clientSession.removeClient("id-123", "Joao");
        assert.strictEqual(ctx.metrics.modalShownCount, 1, "Exibe modal");
        assert.ok(!ctx.metrics.endpointsCalled.some(e => e.endpoint === "remover_cliente_portable"), "Não deve chamar endpoint");
    }

    // Teste 8: Confirmar novo cliente (Sucesso)
    {
        const ctx = setupEnvironment();
        ctx.dom.inputNovo.value = "Novo LTDA ";
        await ctx.Phoenix.features.clientSession.confirmNewClient();
        assert.ok(ctx.metrics.endpointsCalled.some(e => e.endpoint === "criar_cliente_portable" && e.args === "Novo LTDA"), "Deve chamar criar");
        assert.ok(ctx.metrics.endpointsCalled.some(e => e.endpoint === "selecionar_cliente" && e.args === "novo-Novo LTDA"), "Deve selecionar o id");
    }

    // Teste 9: Confirmar novo cliente (Vazio)
    {
        const ctx = setupEnvironment();
        ctx.dom.inputNovo.value = "   ";
        await ctx.Phoenix.features.clientSession.confirmNewClient();
        assert.ok(!ctx.metrics.endpointsCalled.some(e => e.endpoint === "criar_cliente_portable"), "Não chama se vazio");
        assert.strictEqual(ctx.dom.inputNovo.style.borderColor, "var(--cor-erro)", "Destaca campo input com erro");
    }

    console.log("\n9 passed, 0 failed");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
