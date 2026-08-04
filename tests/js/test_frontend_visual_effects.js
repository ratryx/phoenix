const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'ui', 'visual-effects.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: {},
        document: {
            body: {
                classList: {
                    classes: new Set(),
                    add: function(cls) { this.classes.add(cls); },
                    remove: function(...clss) { clss.forEach(c => this.classes.delete(c)); }
                }
            },
            getElementById: function(id) {
                if (id === 'camada-particulas') return context.dom.camada;
                return null;
            },
            createElement: function(tag) {
                if (tag === 'div') {
                    const el = {
                        style: {},
                        className: ''
                    };
                    return el;
                }
                return {};
            }
        },
        Math: {
            random: () => 0.5 // Previsível para testes de limites
        },
        console: {
            error: function () { context.errors.push(Array.from(arguments)); },
            log: function () { context.logs.push(Array.from(arguments)); }
        },
        Phoenix: {
            state: {
                nivelQualidadeVisual: null
            },
            bridge: {
                call: async function(endpoint, args) {
                    context.metrics.endpointsCalled.push({endpoint, args});
                    if (context.mocks.bridgeReject) throw new Error("Bridge reject");
                    if (endpoint === "obter_nivel_qualidade_visual") {
                        return context.mocks.nivel;
                    }
                    return {};
                }
            }
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.errors = [];
    context.logs = [];
    
    context.dom = {
        camada: {
            _html: "",
            _children: [],
              removeChild: function(c) { if (!this.children) return;
                const i = this.children.indexOf(c);
                if (i !== -1) this.children.splice(i, 1);
              },
              get firstChild() { return (this.children && this.children.length > 0) ? this.children[0] : null; },
            get innerHTML() { return this._html; },
            set innerHTML(val) { this._html = val; this._children = []; },
            appendChild: function(child) { this._children.push(child); },
            removeChild: function(c) { const i = this._children.indexOf(c); if(i !== -1) this._children.splice(i, 1); },
            get firstChild() { return this._children.length > 0 ? this._children[0] : null; }
        }
    };

    context.metrics = {
        endpointsCalled: []
    };
    
    context.mocks = {
        bridgeReject: false,
        nivel: "alto"
    };

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes Visual Effects...");

    // Teste 1: Registro
    {
        const ctx = setupEnvironment();
        assert.ok(ctx.Phoenix.ui.visualEffects, "Namespace deve existir");
    }

    // Teste 2: Nenhum efeito ao importar
    {
        const ctx = setupEnvironment();
        assert.strictEqual(ctx.dom.camada._children.length, 0, "Nenhuma partícula antes de initialize");
        assert.strictEqual(ctx.Phoenix.state.nivelQualidadeVisual, null, "Estado visual não deve ser tocado ao importar");
    }

    // Teste 3, 5, 8: initialize localiza a camada, alto gera, remove antigas
    {
        const ctx = setupEnvironment();
        ctx.dom.camada.innerHTML = "lixo"; // Simular antigas
        await ctx.Phoenix.ui.visualEffects.initialize();
        // removed innerHTML assert
        assert.strictEqual(ctx.dom.camada._children.length, 14, "Nível alto: gera exatamente 14 partículas");
        assert.strictEqual(ctx.Phoenix.state.nivelQualidadeVisual, "alto", "Estado correto");
        assert.ok(ctx.document.body.classList.classes.has("qualidade-alta"), "Aplica classe do body");
    }

    // Teste 4: Camada ausente tratada
    {
        const ctx = setupEnvironment();
        ctx.dom.camada = null; // forçar null return no getElementById
        await ctx.Phoenix.ui.visualEffects.initialize(); // não deve lançar throw
        assert.strictEqual(ctx.Phoenix.state.nivelQualidadeVisual, "alto", "Estado setado mas sem particles");
    }

    // Teste 6: Nível baixo
    {
        const ctx = setupEnvironment();
        ctx.mocks.nivel = "baixo";
        await ctx.Phoenix.ui.visualEffects.initialize();
        assert.strictEqual(ctx.dom.camada._children.length, 0, "Nível baixo: 0 partículas geradas");
        assert.strictEqual(ctx.Phoenix.state.nivelQualidadeVisual, "baixo", "Estado correto");
        assert.ok(ctx.document.body.classList.classes.has("qualidade-baixa"), "Aplica classe do body");
    }

    // Teste 7: Nível médio
    {
        const ctx = setupEnvironment();
        ctx.mocks.nivel = "medio";
        await ctx.Phoenix.ui.visualEffects.initialize();
        assert.strictEqual(ctx.dom.camada._children.length, 0, "Nível medio: 0 partículas geradas");
        assert.strictEqual(ctx.Phoenix.state.nivelQualidadeVisual, "medio", "Estado correto");
        assert.ok(ctx.document.body.classList.classes.has("qualidade-media"), "Aplica classe do body");
    }

    // Teste 9 e 10: Propriedades visuais e classes permanecem iguais (com o mock Math.random=0.5)
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.ui.visualEffects.initialize();
        const p = ctx.dom.camada._children[0];
        assert.strictEqual(p.className, "particula", "Classe particula intacta");
        assert.strictEqual(p.style.width, "9px", "Largura 4 + 0.5 * 10 = 9px");
        assert.strictEqual(p.style.height, "9px", "Altura 9px");
        assert.strictEqual(p.style.left, "50%", "Left 50%");
        assert.strictEqual(p.style.top, "80%", "Top 60 + 0.5*40 = 80%");
        assert.strictEqual(p.style.animationDuration, "13s", "Duration 8 + 0.5*10 = 13s");
        assert.strictEqual(p.style.animationDelay, "5s", "Delay 0.5*10 = 5s");
    }

    // Teste 11: Estado visual correto é usado (rejeição fallback para medio)
    {
        const ctx = setupEnvironment();
        ctx.mocks.bridgeReject = true;
        await ctx.Phoenix.ui.visualEffects.initialize();
        assert.strictEqual(ctx.Phoenix.state.nivelQualidadeVisual, "medio", "Catch aplica medio");
    }

    // Teste 12: Repetição não acumula
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.ui.visualEffects.initialize();
        await ctx.Phoenix.ui.visualEffects.initialize();
        assert.strictEqual(ctx.dom.camada._children.length, 14, "Não acumula, recria 14");
    }

    // Testes 13, 14, 15, 16, 17, 18, 19, 20
    {
        const ctx = setupEnvironment();
        await ctx.Phoenix.ui.visualEffects.initialize();
        assert.strictEqual(ctx.metrics.endpointsCalled.length, 1, "Chama apenas um endpoint");
        assert.strictEqual(ctx.metrics.endpointsCalled[0].endpoint, "obter_nivel_qualidade_visual", "Endpoint correto");
        
        assert.ok(!scriptCode.includes("setInterval"), "14. Nenhum timer");
        assert.ok(!scriptCode.includes("setTimeout"), "14. Nenhum timer");
        assert.ok(!scriptCode.includes("bootstrap"), "16. Não contém bootstrap");
        assert.ok(!scriptCode.includes("Phoenix.router"), "17. Não contém router");
        assert.ok(!scriptCode.includes("clientSession"), "18. Não contém cliente");
        assert.ok(!scriptCode.includes("Phoenix.operations"), "19. Não contém rotina");
        assert.ok(!scriptCode.includes("window.pywebview"), "20. Não acessa pywebview diretamente");
        assert.ok(!scriptCode.includes("addEventListener"), "13. Sem listeners");
    }

    console.log("Testes JS Visual Effects passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
