const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

// Configuração do mock do ambiente do navegador
const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'pages', 'servicos.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: {},
        document: {
            getElementById: function (id) {
                if (id === 'conteudo-servicos') {
                    return context.container;
                }
                if (id === 'btn-atualizar-servicos') {
                    return context.btnAtualizar;
                }
                return null;
            }
        },
        console: {
            error: function () { context.errors.push(Array.from(arguments)); },
            log: function () { context.logs.push(Array.from(arguments)); }
        },
        Phoenix: {
            pages: {},
            bridge: {
                call: async function (endpoint, payload) {
                    context.bridgeCalls.push({ endpoint, payload });
                    if (context.mockBridgeResult !== undefined) {
                        return context.mockBridgeResult;
                    }
                    return { job_id: 'fake-job-id' };
                }
            },
            jobs: {
                awaitJob: async function (job_id) {
                    context.jobCalls.push(job_id);
                    if (context.mockJobResult !== undefined) {
                        return context.mockJobResult;
                    }
                    return { ok: true };
                }
            },
            ui: {
                feedback: {
                    mostrarOverlay: function (msg) { context.overlays.push(msg); },
                    esconderOverlay: function () { context.overlaysHidden++; }
                }
            },
            operations: {
                restorePoint: {
                    runProtected: async function (fn) {
                        context.runProtectedCalls++;
                        if (context.mockRunProtectedAction) {
                            return context.mockRunProtectedAction(fn);
                        }
                        return fn();
                    }
                }
            }
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.container = {
        innerHTML: '',
        listeners: {},
        querySelectorAll: function (sel) {
            if (sel === '.toggle') {
                return context.toggles;
            }
            return [];
        }
    };
    context.btnAtualizar = {
        listeners: {},
        dataset: {},
        addEventListener: function (evt, fn) {
            this.listeners[evt] = fn;
        }
    };
    context.toggles = [];
    context.errors = [];
    context.logs = [];
    context.bridgeCalls = [];
    context.jobCalls = [];
    context.overlays = [];
    context.overlaysHidden = 0;
    context.runProtectedCalls = 0;

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes da página Serviços...");

    // Teste 1: Registro e namespace
    {
        const ctx = setupEnvironment();
        assert.ok(ctx.Phoenix.pages.servicos, "Namespace Phoenix.pages.servicos deve existir");
        assert.strictEqual(typeof ctx.Phoenix.pages.servicos.load, 'function', "load deve ser uma função");
        assert.strictEqual(ctx.bridgeCalls.length, 0, "Não deve chamar bridge na importação");
    }

    // Teste 2: Listeners e Refresh button
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.pages.servicos.load();
        assert.strictEqual(ctx.btnAtualizar.dataset.eventosRegistrados, "true", "Deve registrar o evento no botão");
        assert.strictEqual(typeof ctx.btnAtualizar.listeners["click"], "function", "Deve associar evento de clique");
    }

    // Teste 3: Listagem de serviços
    {
        const ctx = setupEnvironment();
        ctx.mockJobResult = {
            ok: true,
            servicos: [
                { nome_servico: "Spooler", nome_amigavel: "Spooler de Impressão", descricao: "Desc", status: "Rodando" },
                { nome_servico: "WSearch", nome_amigavel: "Windows Search", descricao: "Desc", status: "Parado" }
            ]
        };
        await ctx.Phoenix.pages.servicos.load();
        
        assert.strictEqual(ctx.bridgeCalls.length, 1);
        assert.strictEqual(ctx.bridgeCalls[0].endpoint, "listar_servicos");
        assert.strictEqual(ctx.jobCalls.length, 1);
        
        assert.ok(ctx.container.innerHTML.includes("Spooler de Impressão"));
        assert.ok(ctx.container.innerHTML.includes("Windows Search"));
        assert.ok(ctx.container.innerHTML.includes("sucesso"), "Spooler deve ter badge sucesso");
        assert.ok(ctx.container.innerHTML.includes("neutro"), "WSearch deve ter badge neutro");
    }

    // Teste 4: Mutação e duplos cliques (Concorrência)
    {
        const ctx = setupEnvironment();
        ctx.mockJobResult = {
            ok: true,
            servicos: [
                { nome_servico: "TestSvc", nome_amigavel: "Test", descricao: "Desc", status: "Rodando" }
            ]
        };
        
        let toggleClicked = null;
        ctx.container.querySelectorAll = function(sel) {
            if (sel === ".toggle") {
                const btn = {
                    dataset: { servico: "TestSvc", ativo: "true" },
                    classList: {
                        toggled: false,
                        toggle: function(cls) { if (cls === "ativo") this.toggled = !this.toggled; }
                    },
                    addEventListener: function(evt, fn) {
                        if (evt === "click") toggleClicked = fn;
                    }
                };
                return [btn];
            }
            return [];
        };

        await ctx.Phoenix.pages.servicos.load();
        assert.ok(toggleClicked, "Listener do toggle deve ser registrado");

        // Preparar a mutação
        ctx.mockJobResult = { ok: true };
        ctx.bridgeCalls = []; // Reset
        
        // Simular um clique
        const promise1 = toggleClicked();
        
        // Simular duplo clique IMEDIATO no MESMO serviço
        const promise2 = toggleClicked();
        
        await Promise.all([promise1, promise2]);
        
        assert.strictEqual(ctx.runProtectedCalls, 1, "Run protected só deve ser acionado 1 vez pro mesmo serviço em caso de duplo clique instantâneo");
        assert.strictEqual(ctx.bridgeCalls.length, 1, "Bridge call só deve ocorrer 1 vez");
        assert.strictEqual(ctx.bridgeCalls[0].endpoint, "desativar_servico");
        assert.strictEqual(ctx.bridgeCalls[0].payload, "TestSvc");
    }

    // Teste 5: Falha na listagem (Estado vazio/Tratamento)
    {
        const ctx = setupEnvironment();
        ctx.mockJobResult = { ok: false, erro: "Acesso negado" };
        await ctx.Phoenix.pages.servicos.load();
        assert.ok(ctx.container.innerHTML.includes("Acesso negado"), "Deve exibir a badge de erro e a mensagem");
    }

    console.log("Todos os testes JS da Página Serviços passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
