const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'pages', 'relatorio.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: {
            // Emulando globals injetados, se houvesse, mas o script se basta
        },
        document: {
            getElementById: function (id) {
                if (id === 'conteudo-relatorio') {
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
            pages: {}
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.container = {
        innerHTML: ''
    };
    context.errors = [];
    context.logs = [];

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes da página Relatório...");

    // Teste 1: Registro e namespace
    {
        const ctx = setupEnvironment();
        assert.ok(ctx.Phoenix.pages.relatorio, "Namespace Phoenix.pages.relatorio deve existir");
        assert.strictEqual(typeof ctx.Phoenix.pages.relatorio.load, 'function', "load deve ser uma função");
        assert.strictEqual(typeof ctx.Phoenix.pages.relatorio.showResult, 'function', "showResult deve ser uma função");
    }

    // Teste 2: Estado vazio com load()
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.pages.relatorio.load();
        assert.ok(ctx.container.innerHTML.includes("Nenhum relatório disponível"), "Deve exibir fallback de vazio ao dar load sem dados");
    }

    // Teste 3: showResult com dados inválidos
    {
        const ctx = setupEnvironment();
        ctx.Phoenix.pages.relatorio.showResult({ ok: false });
        assert.ok(ctx.container.innerHTML.includes("Falha ao processar relatório"), "Deve exibir mensagem de erro de renderização para payload sem antes/depois");
        assert.ok(ctx.container.innerHTML.includes("badge erro"));
    }

    // Teste 4: showResult com sucesso (Melhora)
    {
        const ctx = setupEnvironment();
        const payload = {
            ok: true,
            antes: { cpu: { uso_percentual: 80.0 }, memoria: { percentual_uso: 90.0, disponivel_gb: 1.0 } },
            depois: { cpu: { uso_percentual: 50.0 }, memoria: { percentual_uso: 60.0, disponivel_gb: 4.0 } },
            espaco_liberado_mb: 2048,
            relatorio_txt: "C:\\Fake\\Relatorio.txt"
        };
        ctx.Phoenix.pages.relatorio.showResult(payload);
        
        // Espaço liberado convertido de 2048 MB para 2.00 GB
        assert.ok(ctx.container.innerHTML.includes("2.00 GB"), "Deve formatar espaço maior que 1024MB para GB");
        
        // Caminho
        assert.ok(ctx.container.innerHTML.includes("C:\\Fake\\Relatorio.txt"), "Deve conter o caminho do relatório");
        
        // Deltas - O CPU foi de 80 para 50 (diferença -30). Como é true (menor é melhor), diferença < 0 = melhora
        // A badge de sucesso deve ter a seta para baixo e "30.0%"
        assert.ok(ctx.container.innerHTML.includes("30.0%"), "Deve formatar variação");
        assert.ok(ctx.container.innerHTML.includes('badge sucesso'), "Deve conter badge sucesso para melhora");
        assert.ok(ctx.container.innerHTML.includes('\u25BC'), "Deve conter seta pra baixo em melhoras em métricas inversas");
    }

    // Teste 5: showResult com piora
    {
        const ctx = setupEnvironment();
        const payload = {
            ok: true,
            antes: { cpu: { uso_percentual: 10.0 }, memoria: { percentual_uso: 10.0, disponivel_gb: 8.0 } },
            depois: { cpu: { uso_percentual: 90.0 }, memoria: { percentual_uso: 90.0, disponivel_gb: 2.0 } }, // Piorou!
            espaco_liberado_mb: 0,
            relatorio_txt: ""
        };
        ctx.Phoenix.pages.relatorio.showResult(payload);
        
        assert.ok(ctx.container.innerHTML.includes("0 B"), "Deve formatar 0 MB pra 0 B");
        assert.ok(ctx.container.innerHTML.includes("Caminho indisponível"), "Deve exibir fallback de txt vazio");
        assert.ok(ctx.container.innerHTML.includes('badge erro'), "Deve exibir badge de erro para piora");
        assert.ok(ctx.container.innerHTML.includes('\u25B2'), "Deve exibir seta pra cima para aumentos em métricas inversas");
    }

    // Teste 6: Neutro
    {
        const ctx = setupEnvironment();
        const payload = {
            ok: true,
            antes: { cpu: { uso_percentual: 10.0 }, memoria: { percentual_uso: 10.0, disponivel_gb: 8.0 } },
            depois: { cpu: { uso_percentual: 10.0 }, memoria: { percentual_uso: 10.0, disponivel_gb: 8.0 } },
            espaco_liberado_mb: null,
            relatorio_txt: "a"
        };
        ctx.Phoenix.pages.relatorio.showResult(payload);
        
        assert.ok(ctx.container.innerHTML.includes("N/D"), "Deve tratar espaço liberado nulo");
        assert.ok(ctx.container.innerHTML.includes('badge neutro'), "Deve exibir badge neutro sem alterações");
        assert.ok(ctx.container.innerHTML.includes('='), "Deve exibir símbolo = para ausência de alterações");
    }

    console.log("Todos os testes JS da Página Relatório passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
