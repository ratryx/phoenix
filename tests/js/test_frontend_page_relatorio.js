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
        navigator: {
            clipboard: {
                writeText: function(text) {
                    return Promise.resolve();
                }
            }
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
            antes: { dados: { cpu: { uso_percentual: 80.0 }, memoria: { percentual_uso: 90.0, disponivel_gb: 1.0 }, discos: [{unidade: "C:", livre_gb: 100}] }, cliente: "John Doe" },
            depois: { dados: { cpu: { uso_percentual: 50.0 }, memoria: { percentual_uso: 60.0, disponivel_gb: 4.0 }, discos: [{unidade: "C:", livre_gb: 150}] } },
            resumo: { espaco_liberado_mb: 2048, otimizacoes_aplicadas: 4, otimizacoes_total: 5 },
            limpeza: { categorias: [{nome: "Cache", arquivos_removidos: 5, arquivos_ignorados: 0, espaco_liberado_bytes: 1024, status: "concluido"}] },
            otimizacoes: { resultados: { "opt1": { ok: true, descricao: "Otimização 1" } }, before_state: { "opt1": { ativo: false } } },
            protecao: { status: "restore_created", mensagem: "OK" },
            analises: {
                startup: { ok: true, total: 10, alto_impacto: 2 },
                smart: { ok: true, discos: [{device_id: "0", nome: "SSD Pro", tipo_midia: "SSD", tamanho_gb: 500, classificacao: "Saudável", confiabilidade: { temperatura_c: 35, horas_uso: 100, wear_percent: 5, erros_leitura: 0, erros_escrita: 0 }, alertas: []}] },
                drivers: { ok: true, resultados: [{nome: "Virtual GPU", fabricante: "Parsec", classificacao: "Adaptador virtual", tipo_adaptador: "virtual"}] }
            },
            recomendacoes: [ { titulo: "Rec 1", descricao: "Desc", nivel: "aviso" } ],
            duracao_segundos: 45,
            relatorio_html: "C:\\Fake\\Relatorio.html"
        };
        ctx.Phoenix.pages.relatorio.showResult({ payload: payload });

        const html = ctx.container.innerHTML;

        // Formatar bytes
        assert.ok(html.includes("2.00 GB"), "Deve formatar espaço maior que 1024MB para GB");

        // Recomendações
        assert.ok(html.includes("Recomendações"), "Deve mostrar bloco de recomendações");
        assert.ok(html.includes("Rec 1"), "Deve renderizar a recomendação");

        // Análises SMART reais
        assert.ok(html.includes("Saúde do Sistema"), "Deve mostrar Saúde do Sistema");
        assert.ok(html.includes("SSD Pro"), "Deve renderizar o nome do disco");
        assert.ok(html.includes("35°C"), "Deve renderizar a temperatura");
        assert.ok(html.includes("5%"), "Deve renderizar desgaste");

        // Achados startup
        assert.ok(html.includes("2 programa(s) de inicialização com potencial impacto"), "Deve exibir a wording correta de startup");

        // Identidade
        assert.ok(html.includes("John Doe"), "Deve exibir o cliente");
        assert.ok(html.includes("45s"), "Deve exibir duração");

        // Drivers virtuais
        assert.ok(html.includes("Virtual GPU"), "Deve exibir drivers");
        assert.ok(html.includes("Adaptador virtual"), "Deve mostrar classificação de driver virtual");

        // Otimizações aplicadas e before state
        assert.ok(html.includes("4 / 5"), "Deve mostrar total de otimizações aplicadas");
        assert.ok(html.includes("Não aplicado"), "Deve mostrar before_state formatado");

        // Totais de Limpeza
        assert.ok(html.includes("TOTAIS"), "Deve mostrar resumo do footer de limpeza");
        assert.ok(html.includes("5"), "Deve mostrar total removidos");

        // CPU/RAM neutro
        assert.ok(html.includes("oscilações momentâneas"), "Deve exibir texto neutro de CPU/RAM");

        // Ações
        assert.ok(html.includes("Abrir relatório HTML"), "Deve exibir CTA Abrir relatório HTML");
        assert.ok(html.includes("Copiar resumo"), "Deve exibir CTA Copiar resumo");
    }

    console.log("Todos os testes JS da Página Relatório passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
