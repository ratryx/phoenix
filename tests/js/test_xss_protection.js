const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function createMockDOM() {
    const context = {
        window: {},
        document: {
            elements: {},
            createElement: function(tag) {
                return {
                    tagName: tag.toUpperCase(),
                    className: '',
                    style: {},
                    dataset: {},
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
                if (!this.elements[id]) {
                    this.elements[id] = {
                        id: id,
                        innerHTML: '',
                        children: [],
                        className: '',
                        style: {},
                        dataset: {},
                        lastElementChild: null,
                        addEventListener: function() {},
                        appendChild: function(c) { this.children.push(c); this.lastElementChild = c; },
                        insertBefore: function(newChild, refChild) { this.children.push(newChild); },
                        classList: { add: function(){}, remove: function(){} },
                        querySelectorAll: function() { return []; }
                    };
                }
                return this.elements[id];
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
                    if (context.mockBridgeResult && !context.mockBridgeResult.isJobResult) return context.mockBridgeResult;
                    return { ok: true, job_id: '123' };
                }
            },
            jobs: {
                awaitJob: async function() { return (context.mockBridgeResult && context.mockBridgeResult.isJobResult) ? context.mockBridgeResult : { ok: true }; }
            },
            ui: {
                feedback: { mostrarOverlay: function () {}, esconderOverlay: function () {} }
            }
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.errors = [];
    context.logs = [];
    return context;
}

function loadScript(context, scriptName) {
    const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'pages', scriptName);
    const scriptCode = fs.readFileSync(scriptPath, 'utf8');
    vm.createContext(context);
    vm.runInContext(scriptCode, context);
}

function findTextContent(node) {
    if (!node) return "";
    let res = "";
    if (node.isTextNode) res += node.textContent;
    if (node._textContent) res += node._textContent;
    for (let c of (node.children || [])) {
        res += findTextContent(c);
    }
    return res;
}

async function testHistorico() {
    const ctx = createMockDOM();
    loadScript(ctx, 'historico.js');
    
    const payload = "<img src=x onerror=\"window.__xss=1\">";
    ctx.mockBridgeResult = {
        ok: true,
        atendimentos: [ { id_atendimento: "1", cliente: payload, data_hora: "2026-07-17" } ]
    };
    
    await ctx.Phoenix.pages.historico.load();
    const container = ctx.document.elements['conteudo-historico'];
    assert.strictEqual(container.innerHTML, "");
    
    const text = findTextContent(container);
    assert.ok(text.includes(payload), "Payload deve estar seguro como texto no Histórico");
}

async function testDiagnostico() {
    const ctx = createMockDOM();
    loadScript(ctx, 'diagnostico.js');
    
    const payload = "<svg onload=\"window.__xss=1\"></svg>";
    ctx.mockBridgeResult = {
        ok: true,
        isJobResult: true,
        dados: {
            cpu: { uso_percentual: 85 },
            memoria: { percentual_uso: 50, disponivel_gb: 4 },
            discos: [],
            processos: [ { name: payload, cpu_percent: 25, memory_percent: 10 } ]
        }
    };
    
    await ctx.Phoenix.pages.diagnostico.load();
    if (ctx.errors.length > 0) console.error("Errors:", ctx.errors);
    
    const container = ctx.document.elements['conteudo-diagnostico'];
    const text = findTextContent(container);
    if (!text.includes(payload)) {
        console.error("Text content was:", text);
        console.error("Children length:", container.children.length);
    }
    assert.ok(text.includes(payload), "Payload de processo deve ser texto seguro");
    

}

async function testOtimizacao() {
    const ctx = createMockDOM();
    loadScript(ctx, 'otimizacao.js');
    
    const payload = "\"><img src=x onerror=alert(1)>";
    ctx.mockBridgeResult = {
        ok: true,
        isJobResult: true,
        entradas: [ { nome: payload, comando: payload, raiz: payload } ]
    };
    
    await ctx.Phoenix.pages.otimizacao.analyzeStartup();
    
    const lista = ctx.document.elements['resultado-startup'];
    assert.strictEqual(lista.innerHTML, "");
    assert.ok(findTextContent(lista).includes(payload), "Payload de startup deve ser texto seguro");
}

async function testServicos() {
    const ctx = createMockDOM();
    loadScript(ctx, 'servicos.js');
    
    const payload = "<script>alert(1)</script>";
    ctx.mockBridgeResult = {
        ok: true,
        isJobResult: true,
        servicos: [ { nome_servico: "S1", nome_amigavel: payload, descricao: payload, status: "Parado" } ]
    };
    
    await ctx.Phoenix.pages.servicos.load();
    
    const tabela = ctx.document.elements['conteudo-servicos'];
    assert.strictEqual(tabela.innerHTML, "");
    assert.ok(findTextContent(tabela).includes(payload), "Payload de serviço deve ser texto seguro");
}

async function runAll() {
    console.log("Iniciando testes de XSS...");
    await testHistorico();
    await testDiagnostico();
    await testOtimizacao();
    await testServicos();
    console.log("Testes de XSS completados e innerHTML não foi abusado.");
}

runAll().catch(err => {
    console.error(err);
    process.exit(1);
});
