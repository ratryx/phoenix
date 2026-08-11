const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'pages', 'relatorio.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: {},
        document: {
            getElementById: function (id) {
                if (id === 'conteudo-relatorio') return context.container;
                return null;
            },
            createElement: function(tag) {
                return {
                    tagName: tag.toUpperCase(),
                    className: '',
                    style: {},
                    children: [],
                    _textContent: '',
                    get textContent() { return this._textContent; },
                    set textContent(val) { this._textContent = val; },
                    appendChild: function(child) { this.children.push(child); }
                };
            },
            createTextNode: function(text) {
                return { isTextNode: true, textContent: text };
            }
        },
        console: {
            error: function () { context.errors.push(Array.from(arguments)); },
            log: function () { context.logs.push(Array.from(arguments)); }
        },
        Phoenix: { pages: {} }
    };
    context.window.Phoenix = context.Phoenix;
    function getHTML(node) {
        if (node.isTextNode) return node.textContent;
        var html = `<${node.tagName || 'div'} class="${node.className || ''}">`;
        for (var i = 0; i < (node.children || []).length; i++) {
            html += getHTML(node.children[i]);
        }
        if (node._textContent) html += node._textContent;
        html += `</${node.tagName || 'div'}>`;
        return html;
    }

    context.container = {
        _innerHTML: '',
        get innerHTML() {
            var html = this._innerHTML;
            for (var i = 0; i < (this.children || []).length; i++) {
                html += getHTML(this.children[i]);
            }
            return html;
        },
        set innerHTML(val) {
            this._innerHTML = val;
            this.children = [];
        },
        children: [],
        appendChild: function(child) {
            this.children.push(child);
        }
    };
    context.errors = [];
    context.logs = [];

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes da página Relatório V3...");

    // Teste 1: Registro e namespace
    {
        const ctx = setupEnvironment();
        assert.ok(ctx.Phoenix.pages.relatorio, "Namespace Phoenix.pages.relatorio deve existir");
        assert.strictEqual(typeof ctx.Phoenix.pages.relatorio.load, 'function', "load deve ser uma função");
        assert.strictEqual(typeof ctx.Phoenix.pages.relatorio.showResult, 'function', "showResult deve ser uma função");
    }

    // Teste 2: showResult com payload nulo
    {
        const ctx = setupEnvironment();
        ctx.Phoenix.pages.relatorio.showResult(null);
        assert.ok(ctx.container.innerHTML.includes("Falha ao carregar relatório"), "Deve exibir erro");
    }

    // Teste 3: showResult V3
    {
        const ctx = setupEnvironment();
        const payload = {
            snapshot_antes: { dados: { cpu: { uso_percentual: 80.0 }, memoria: { percentual_uso: 90.0, disponivel_gb: 1.0 }, discos: [{unidade: "C:", livre_gb: 100}] } },
            snapshot_depois: { dados: { cpu: { uso_percentual: 50.0 }, memoria: { percentual_uso: 60.0, disponivel_gb: 4.0 }, discos: [{unidade: "C:", livre_gb: 150}] } },
            resumo: { espaco_liberado_mb: 2048, otimizacoes_aplicadas: 4, otimizacoes_total: 5 },
            limpeza: { categorias: [] },
            otimizacoes: { resultados: { "opt1": { ok: true, descricao: "Otimização 1" } } },
            protecao: { status: "restore_created", mensagem: "OK" },
            analises: { smart: { ok: true, discos: [{device_id: "0", tipo_midia: "SSD", classificacao: "Saudável"}] } },
            recomendacoes: [ { titulo: "Rec 1", descricao: "Desc", nivel: "aviso" } ]
        };
        ctx.Phoenix.pages.relatorio.showResult({ payload: payload });
        
        const html = ctx.container.innerHTML;
        
        // Formatar bytes
        assert.ok(html.includes("2.00 GB"), "Deve formatar espaço maior que 1024MB para GB");
        
        // Recomendações
        assert.ok(html.includes("Recomendações"), "Deve mostrar bloco de recomendações");
        assert.ok(html.includes("Rec 1"), "Deve renderizar a recomendação");
        
        // Análises SMART
        assert.ok(html.includes("Saúde do Sistema"), "Deve mostrar Saúde do Sistema");
        assert.ok(html.includes("Saud"), "Deve renderizar o estado do disco");
        
        // Otimizações aplicadas
        assert.ok(html.includes("4 / 5"), "Deve mostrar total de otimizações aplicadas");
    }

    console.log("Todos os testes JS da Página Relatório passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
