const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'operations', 'routine.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: {},
        document: {},
        console: {
            error: function () { context.errors.push(Array.from(arguments)); },
            log: function () { context.logs.push(Array.from(arguments)); }
        },
        Phoenix: {
            operations: {
                restorePoint: {
                    runProtected: async function(fn) {
                        context.metrics.runProtectedCalled = true;
                        if (!context.mocks.abortRestorePoint) {
                            return await fn();
                        }
                    }
                }
            },
            bridge: {
                call: async function(endpoint, args) {
                    context.metrics.endpointsCalled.push(endpoint);
                    if (context.mocks.bridgeReject) throw new Error("Bridge reject");
                    if (endpoint === "executar_rotina_completa") {
                        if (context.mocks.noJobId) return {};
                        return { job_id: "job123" };
                    }
                    return {};
                }
            },
            jobs: {
                awaitJob: async function(id) {
                    context.metrics.jobWaited = id;
                    if (context.mocks.jobReject) throw new Error("Job reject");
                    return context.mocks.jobResult || { ok: true, relatorio_txt: "C:\\Fake.txt" };
                }
            },
            ui: {
                feedback: {
                    mostrarOverlay: function(msg, block) { context.metrics.overlayShown = true; },
                    esconderOverlay: function(all, instant) { context.metrics.overlayHidden = true; },
                    confirmarModal: async function(titulo, msg, icone) {
                        context.metrics.modalShown = true;
                        return true;
                    }
                }
            },
            router: {
                navigate: function(route) {
                    context.metrics.navigatedTo = route;
                }
            },
            pages: {
                relatorio: {
                    showResult: function(res) {
                        context.metrics.resultShown = res;
                    }
                }
            }
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.errors = [];
    context.logs = [];
    context.metrics = {
        endpointsCalled: [],
        runProtectedCalled: false,
        jobWaited: null,
        overlayShown: false,
        overlayHidden: false,
        modalShown: false,
        navigatedTo: null,
        resultShown: null
    };
    context.mocks = {
        abortRestorePoint: false,
        bridgeReject: false,
        jobReject: false,
        noJobId: false,
        jobResult: null
    };

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes da operação Routine...");

    // Teste 1: Módulo registrado
    {
        const ctx = setupEnvironment();
        assert.ok(ctx.Phoenix.operations.routine, "Namespace Phoenix.operations.routine deve existir");
        assert.strictEqual(typeof ctx.Phoenix.operations.routine.execute, 'function', "execute deve ser uma função");
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 0, "Nenhum endpoint deve ser chamado ao importar");
    }

    // Teste 2: Execução com sucesso
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.operations.routine.execute();
        assert.ok(ctx.metrics.runProtectedCalled, "Deve usar restore point (runProtected)");
        assert.ok(ctx.metrics.endpointsCalled.includes("executar_rotina_completa"), "Deve chamar executar_rotina_completa");
        assert.strictEqual(ctx.metrics.jobWaited, "job123", "Deve aguardar o job");
        assert.strictEqual(ctx.metrics.navigatedTo, "relatorio", "Deve navegar para relatorio");
        assert.ok(ctx.metrics.resultShown, "Deve entregar o resultado");
        assert.ok(!ctx.metrics.modalShown, "Não deve exibir modal em caso de sucesso");
        
        // Verifica se a flag foi liberada
        const secondCallMetrics = setupEnvironment().metrics; // apenas para pegar um obj novo? Nao, vou usar ctx original
        await ctx.Phoenix.operations.routine.execute();
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 2, "Flag deve ter liberado para segunda chamada");
    }

    // Teste 3: Abortar restore point
    {
        const ctx = setupEnvironment();
        ctx.mocks.abortRestorePoint = true;
        await ctx.Phoenix.operations.routine.execute();
        assert.ok(ctx.metrics.runProtectedCalled, "Tenta o restore point");
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 0, "Não deve prosseguir se restore point abortar");
        
        // Flag deve liberar
        ctx.mocks.abortRestorePoint = false;
        await ctx.Phoenix.operations.routine.execute();
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 1, "Flag deve liberar após abort do restore point");
    }

    // Teste 4: Concorrência
    {
        const ctx = setupEnvironment();
        let resolveJob;
        ctx.Phoenix.jobs.awaitJob = () => new Promise(resolve => { resolveJob = resolve; });
        
        const p1 = ctx.Phoenix.operations.routine.execute();
        const p2 = ctx.Phoenix.operations.routine.execute();
        
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 1, "Deve ignorar duplo clique (concorrência)");
        // aguardar um ciclo de event loop para garantir que awaitJob foi chamado
        await new Promise(r => setImmediate(r));
        resolveJob({ ok: true });
        await p1;
        await p2;
    }

    // Teste 5: {ok: false} do backend
    {
        const ctx = setupEnvironment();
        ctx.mocks.jobResult = { ok: false, erro: "Falha de teste" };
        await ctx.Phoenix.operations.routine.execute();
        assert.ok(ctx.metrics.modalShown, "Deve exibir modal de erro quando ok=false");
        assert.strictEqual(ctx.metrics.navigatedTo, null, "Não deve navegar para relatório em falha");
        assert.strictEqual(ctx.metrics.resultShown, null, "Não deve entregar resultado em falha");
        
        // Flag liberta
        await ctx.Phoenix.operations.routine.execute();
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 2, "Flag deve ter liberado após erro {ok: false}");
    }

    // Teste 6: Bridge reject
    {
        const ctx = setupEnvironment();
        ctx.mocks.bridgeReject = true;
        await ctx.Phoenix.operations.routine.execute();
        assert.ok(ctx.metrics.overlayHidden, "Deve esconder overlay na exception de bridge");
        // Flag deve liberar
        ctx.mocks.bridgeReject = false;
        await ctx.Phoenix.operations.routine.execute();
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 2, "Flag deve liberar após exception");
    }

    console.log("Testes JS da operação Routine passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
