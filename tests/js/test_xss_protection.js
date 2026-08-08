const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function setupEnvironment() {
    const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'pages', 'historico.js');
    const scriptCode = fs.readFileSync(scriptPath, 'utf8');

    const context = {
        window: {},
        document: {
            createElement: function(tag) {
                return {
                    tagName: tag.toUpperCase(),
                    className: '',
                    children: [],
                    _textContent: '',
                    get textContent() { return this._textContent; },
                    set textContent(val) { this._textContent = val; },
                    appendChild: function(child) { this.children.push(child); }
                };
            },
            createTextNode: function(text) {
                return { isTextNode: true, textContent: text };
            },
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
                    return context.mockBridgeResult || { ok: true, atendimentos: [] };
                }
            },
            ui: {
                feedback: {
                    mostrarOverlay: function () {},
                    esconderOverlay: function () {}
                }
            }
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.container = {
        innerHTML: '',
        children: [],
        appendChild: function(c) { this.children.push(c); }
    };
    context.errors = [];
    context.logs = [];

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes XSS de Histórico...");

    const ctx = setupEnvironment();
    // Payload malicioso
    const payloadXss = "<img src=x onerror=alert(1)>";
    ctx.mockBridgeResult = {
        ok: true,
        atendimentos: [
            { id_atendimento: "1", cliente: payloadXss, data_hora: "2026-07-17" }
        ]
    };
    await ctx.Phoenix.pages.historico.load();
    
    // Verificamos que o innerHTML NÃO foi usado para injetar a string inteira
    assert.strictEqual(ctx.container.innerHTML, ""); 
    
    // Verificamos os nós na árvore virtual
    assert(ctx.container.children.length > 0);
    const card = ctx.container.children[0];
    const table = card.children.find(c => c.tagName === 'TABLE');
    const tbody = table.children.find(c => c.tagName === 'TBODY');
    const tr = tbody.children[0];
    
    // A segunda célula (td) deve conter o payload textContent e não parsed
    const tdCliente = tr.children[1];
    assert.strictEqual(tdCliente.textContent, payloadXss, "Payload não foi injetado como HTML, texto preservado com segurança.");

    console.log("Testes XSS passaram (innerHTML não foi abusado).");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
