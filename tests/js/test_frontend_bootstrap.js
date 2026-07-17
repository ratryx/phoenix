const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scriptPath = path.join(__dirname, '..', '..', 'gui', 'app.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: { location: { hash: '' }, document: { body: { classList: { add: () => {}, remove: () => {} } } } },
        document: {
            getElementById: function() { return null; },
            querySelectorAll: function() { return []; },
            querySelector: function() { return null; },
            body: { classList: { add: () => {}, remove: () => {} } }
        },
        console: {
            error: function () { context.errors.push(Array.from(arguments)); },
            log: function () { context.logs.push(Array.from(arguments)); }
        },
        Phoenix: {
            state: {},
            bridge: {
                whenReady: async function() {
                    context.metrics.bridgeWaited = true;
                },
                call: async function(endpoint) {
                    context.metrics.endpoints.push(endpoint);
                    return {};
                }
            },
            router: {
                setPageLoader: function(cb) { context.metrics.pageLoaderSet = true; },
                initialize: function() { context.metrics.routerInitialized = true; }
            },
            ui: {
                windowControls: {
                    initialize: function() { context.metrics.windowControlsInitialized = true; }
                },
                visualEffects: {
                    initialize: async function() { context.metrics.visualEffectsInitialized = true; }
                }
            },
            features: {
                clientSession: {
                    initialize: async function() { context.metrics.clientSessionInitialized = true; }
                }
            },
            pages: {
                inicio: {
                    carregarHardwareInicial: async function() { context.metrics.hardwareCarregado = true; },
                    iniciarAtualizacaoTempoReal: function() { context.metrics.tempoReal = true; },
                    load: function() { context.metrics.inicioLoad = true; }
                },
                diagnostico: { load: () => {} },
                hardware: { load: () => {} },
                hwmonitor: { load: () => {} },
                limpeza: { load: () => {} },
                otimizacao: { load: () => {} },
                servicos: { load: () => {} },
                historico: { load: () => {} },
                relatorio: { load: () => {} }
            },
            operations: {
                routine: {
                    execute: () => { context.metrics.routineExecuted = true; }
                }
            }
        }
    };
    
    context.window.Phoenix = context.Phoenix;
    context.errors = [];
    context.logs = [];
    
    context.metrics = {
        bridgeWaited: false,
        pageLoaderSet: false,
        windowControlsInitialized: false,
        clientSessionInitialized: false,
        hardwareCarregado: false,
        tempoReal: false,
        routerInitialized: false,
        endpoints: [],
        routineExecuted: false,
        inicioLoad: false,
        visualEffectsInitialized: false
    };

    vm.createContext(context);
    // app.js invoca bootstrap imediatamente.
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes Bootstrap (app.js)...");

    // Teste 1: Fluxo de inicialização correto
    {
        const ctx = setupEnvironment();
        // app.js async bootstrap
        await new Promise(resolve => setTimeout(resolve, 50)); 
        assert.ok(ctx.metrics.pageLoaderSet, "Deve registrar page loader do router no escopo");
        assert.ok(ctx.metrics.bridgeWaited, "Deve aguardar a bridge");
        assert.ok(ctx.metrics.windowControlsInitialized, "Deve inicializar window controls");
        assert.ok(ctx.metrics.clientSessionInitialized, "Deve inicializar client session");
        assert.ok(ctx.metrics.hardwareCarregado, "Deve carregar hardware inicial");
        assert.ok(ctx.metrics.tempoReal, "Deve iniciar att tempo real");
        assert.ok(ctx.metrics.routerInitialized, "Deve inicializar o router");
        assert.ok(ctx.metrics.visualEffectsInitialized, "Deve inicializar efeitos visuais");
        
        assert.ok(!ctx.metrics.routineExecuted, "Não deve executar rotina na inicialização");
    }

    console.log("Testes JS Bootstrap passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
