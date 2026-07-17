const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'ui', 'window-controls.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: {
            addEventListener: function(evt, handler) {
                context.metrics.windowListeners.push({evt, handler});
            }
        },
        document: {
            getElementById: function(id) {
                if (id === 'btn-minimizar') return context.dom.btnMin;
                if (id === 'btn-fechar') return context.dom.btnFechar;
                return null;
            },
            querySelector: function(sel) {
                if (sel === '.barra-titulo') return context.dom.titleBar;
                return null;
            },
            querySelectorAll: function(sel) {
                if (sel === '.cabecalho-pagina') return [context.dom.cabecalho];
                return [];
            }
        },
        requestAnimationFrame: function(cb) {
            context.metrics.rAfCalled = true;
            return 123;
        },
        cancelAnimationFrame: function(id) {
            context.metrics.cAfCalled = true;
        },
        console: {
            error: function () { context.errors.push(Array.from(arguments)); },
            log: function () { context.logs.push(Array.from(arguments)); }
        },
        Phoenix: {
            bridge: {
                isReady: () => context.mocks.bridgeReady,
                call: async function(endpoint, ...args) {
                    context.metrics.endpointsCalled.push({endpoint, args});
                }
            }
        }
    };
    
    // dom elements
    function createEl() {
        const el = {
            listeners: {},
            addEventListener: function(evt, handler) {
                if (!this.listeners[evt]) this.listeners[evt] = [];
                this.listeners[evt].push(handler);
            },
            fire: function(evt, evtObj) {
                if (this.listeners[evt]) {
                    this.listeners[evt].forEach(h => h(evtObj));
                }
            }
        };
        return el;
    }

    context.window.Phoenix = context.Phoenix;
    context.errors = [];
    context.logs = [];
    
    context.dom = {
        btnMin: createEl(),
        btnFechar: createEl(),
        titleBar: createEl(),
        cabecalho: createEl()
    };

    context.metrics = {
        endpointsCalled: [],
        windowListeners: [],
        rAfCalled: false,
        cAfCalled: false
    };
    
    context.mocks = {
        bridgeReady: true
    };

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes Window Controls...");

    // Teste 1: Registro
    {
        const ctx = setupEnvironment();
        assert.ok(ctx.Phoenix.ui.windowControls, "Namespace deve existir");
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 0, "Nenhum endpoint ao importar");
        assert.strictEqual(ctx.metrics.windowListeners.length, 0, "Nenhum listener registrado apenas ao importar");
    }

    // Teste 2: Botões simples
    {
        const ctx = setupEnvironment();
        ctx.Phoenix.ui.windowControls.initialize();
        
        ctx.dom.btnMin.fire("click", {});
        assert.ok(ctx.metrics.endpointsCalled.some(e => e.endpoint === "minimizar_janela"));
        
        ctx.dom.btnFechar.fire("click", {});
        assert.ok(ctx.metrics.endpointsCalled.some(e => e.endpoint === "fechar_janela"));
    }

    // Teste 3: Drag
    {
        const ctx = setupEnvironment();
        ctx.Phoenix.ui.windowControls.initialize();
        
        // Simular mousedown na titlebar
        const evtDown = {
            screenX: 100, screenY: 200, clientX: 10, clientY: 20,
            target: { closest: () => false }
        };
        ctx.dom.titleBar.fire("mousedown", evtDown);
        
        // Deve chamar iniciar_drag e solicitar Animation Frame
        assert.ok(ctx.metrics.endpointsCalled.some(e => e.endpoint === "iniciar_drag" && e.args[0] === 100 && e.args[1] === 200), "iniciar_drag chamado");
        assert.ok(ctx.metrics.rAfCalled, "Solicitou frame de animação");
        
        // Simular mouseup no window (libera drag)
        const mouseUpHandler = ctx.metrics.windowListeners.find(l => l.evt === "mouseup").handler;
        mouseUpHandler();
        
        assert.ok(ctx.metrics.endpointsCalled.some(e => e.endpoint === "parar_drag"));
        assert.ok(ctx.metrics.cAfCalled, "Cancelou frame de animação");
    }

    // Teste 4: Elemento interativo bloqueia drag
    {
        const ctx = setupEnvironment();
        ctx.Phoenix.ui.windowControls.initialize();
        const evtDown = {
            target: { closest: (sel) => sel === "button" ? true : false } // simulando click num button dentro da titlebar
        };
        ctx.dom.titleBar.fire("mousedown", evtDown);
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 0, "Não deve iniciar drag em elementos interativos");
    }

    console.log("Testes JS Window Controls passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
