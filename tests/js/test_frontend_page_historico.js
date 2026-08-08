const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

// Configuração do mock do ambiente do navegador
const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'pages', 'historico.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: {},
        document: {
            getElementById: function (id) {
                if (id === 'conteudo-historico') {
                    return context.container;
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
                    return { ok: true, atendimentos: [] };
                }
            },
            jobs: {
                awaitJob: async function (job_id) {
                    context.jobCalls.push(job_id);
                    return { ok: true };
                }
            },
            ui: {
                feedback: {
                    mostrarOverlay: function (msg) { context.overlays.push(msg); },
                    esconderOverlay: function () { context.overlaysHidden++; }
                }
            }
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.container = {
        innerHTML: ''
    };
    context.errors = [];
    context.logs = [];
    context.bridgeCalls = [];
    context.jobCalls = [];
    context.overlays = [];
    context.overlaysHidden = 0;

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes da página Histórico...");

    // Teste 1: Registro e namespace
    {
        const ctx = setupEnvironment();
        assert.ok(ctx.Phoenix.pages.historico, "Namespace Phoenix.pages.historico deve existir");
        assert.strictEqual(typeof ctx.Phoenix.pages.historico.load, 'function', "load deve ser uma função");
        assert.strictEqual(ctx.bridgeCalls.length, 0, "Não deve chamar bridge na importação");
    }

    // Teste 2: Listagem de histórico vazio
    {
        const ctx = setupEnvironment();
        ctx.mockBridgeResult = {
            ok: true,
            atendimentos: []
        };
        await ctx.Phoenix.pages.historico.load();
        
        assert.strictEqual(ctx.bridgeCalls.length, 1);
        assert.strictEqual(ctx.bridgeCalls[0].endpoint, "obter_historico");
        assert.strictEqual(ctx.jobCalls.length, 0);
        
        assert.ok(ctx.container.innerHTML.includes("Nenhum atendimento registrado ainda"), "Deve exibir mensagem de estado vazio");
        assert.strictEqual(ctx.overlaysHidden, 1, "Overlay deve ser escondido após consultar");
    }

    // Teste 3: Listagem de histórico preenchido
    {
        const ctx = setupEnvironment();
        ctx.mockBridgeResult = {
            ok: true,
            atendimentos: [
                { id_atendimento: "20260717", cliente: "João Silva", data_hora: "2026-07-17 14:00" },
                { id_atendimento: "20260718", cliente: "Maria Souza", data_hora: "2026-07-18 10:30" }
            ]
        };
        await ctx.Phoenix.pages.historico.load();
        
        assert.ok(ctx.container.innerHTML.includes("João Silva"), "Deve conter Cliente João Silva");
        assert.ok(ctx.container.innerHTML.includes("Maria Souza"), "Deve conter Cliente Maria Souza");
        assert.ok(ctx.container.innerHTML.includes("20260717"), "Deve conter ID do atendimento");
        assert.ok(ctx.container.innerHTML.includes("tabela-dados"), "Deve renderizar na tabela de dados");
    }

    // Teste 4: Falha na listagem (Estado erro)
    {
        const ctx = setupEnvironment();
        ctx.mockBridgeResult = { ok: false, erro: "Falha de disco" };
        await ctx.Phoenix.pages.historico.load();
        assert.ok(ctx.container.innerHTML.includes("Falha de disco"), "Deve exibir a badge de erro e a mensagem");
        assert.ok(ctx.container.innerHTML.includes("badge erro"));
        assert.strictEqual(ctx.overlaysHidden, 1);
    }

    console.log("Todos os testes JS da Página Histórico passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
