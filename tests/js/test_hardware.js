const assert = require('assert');

// Mock DOM
const domElements = {};
global.document = {
    getElementById: (id) => {
        if (!domElements[id]) {
            domElements[id] = {
                id,
                style: {},
                dataset: {},
                textContent: "",
                innerHTML: "",
                classList: {
                    classes: new Set(),
                    add: function(c) { this.classes.add(c); },
                    remove: function(c) { this.classes.delete(c); },
                    contains: function(c) { return this.classes.has(c); }
                },
                addEventListener: function(evt, cb) {
                    this['on' + evt] = cb;
                },
                removeEventListener: function(evt, cb) {
                    if (this['on' + evt] === cb) delete this['on' + evt];
                },
                appendChild: function(child) {
                    if (!this.children) this.children = [];
                    this.children.push(child);
                }
            };
        }
        return domElements[id];
    },
    createElement: (tag) => {
        return { tag, style: {}, classList: { add: () => {}, remove: () => {} }, appendChild: () => {} };
    }
};

let _callCount = 0;
let _jobResultMock = null;
let _forcarRescanMock = null;

// Setup global context for JS loading
global.setTimeout = (cb) => cb();
global.window = {
    setTimeout: global.setTimeout,
    document: global.document
};

// Carregar namespace
require('../../gui/js/core/namespace.js');

// Mock Phoenix bridge/jobs
Object.assign(global.window.Phoenix, {
    bridge: {
        call: async (method) => {
            _callCount++;
            if (method === "obter_inventario_atual") {
                return {
                    status: "completo",
                    sistema: { os_nome: "Windows 11", placa_mae: { modelo: "B550" }, bios: { versao: "1.0" } },
                    cpu: { modelo: "Ryzen 5" },
                    memoria: { total_instalada_gb: 16 },
                    gpus: [{ nome: "GTX 1060", tipo: "dedicada", vram_status: "exata", vram_total_mb: 6144 }],
                    armazenamento: { discos_fisicos: [], volumes: [] }
                };
            }
            if (method === "forcar_rescan_hardware") {
                if (_forcarRescanMock) {
                    if (_forcarRescanMock.throw) throw new Error(_forcarRescanMock.throw);
                    return _forcarRescanMock.return;
                }
                return { job_id: "job-123" };
            }
        }
    },
    jobs: {
        awaitJob: async (jobId) => {
            return _jobResultMock;
        }
    }
});

global.window.Phoenix.ui.visualEffects = {
    refresh: () => {
        global.visualEffectsRefreshed = true;
    }
};

global.window.Phoenix.pages = {
    inicio: {
        load: () => {
            global.inicioLoaded = true;
        }
    }
};

global.Phoenix = global.window.Phoenix;

// Carregar feedback real
require('../../gui/js/ui/feedback.js');

// Carregar hardware real
require('../../gui/js/pages/hardware.js');

function erroFoiMostrado() {
    const overlay = domElements['overlay-processando'];
    const icone = domElements['overlay-icone'];
    return overlay && overlay.classList.contains('visivel') === false && icone && icone.textContent === '⚠️';
}

function sucessoFoiMostrado() {
    const overlay = domElements['overlay-processando'];
    const icone = domElements['overlay-icone'];
    return overlay && overlay.classList.contains('visivel') === false && icone && icone.textContent === '✅';
}

function resetMocks() {
    global.visualEffectsRefreshed = false;
    global.inicioLoaded = false;
    _callCount = 0;
    _jobResultMock = null;
    _forcarRescanMock = null;
    if (domElements['hw-conteudo']) domElements['hw-conteudo'].innerHTML = '';

    // Reset overlay mocks
    if (domElements['overlay-processando']) domElements['overlay-processando'].classList.classes.clear();
    if (domElements['overlay-icone']) domElements['overlay-icone'].textContent = '';
}

async function runTests() {
    console.log("Rodando testes test_hardware.js...");
    await Phoenix.pages.hardware.load();
    const btn = document.getElementById('btn-atualizar-hardware');

    // 1. Fluxo de Sucesso Completo
    resetMocks();
    _jobResultMock = { ok: true, hardware: { status: "completo" } };
    await btn.onclick();
    assert.ok(!global.inicioLoaded, "NÃO deve chamar inicio.load no sucesso");
    assert.ok(global.visualEffectsRefreshed, "Deve atualizar efeitos no sucesso");
    assert.ok(!btn.disabled, "Botão deve ser reabilitado");
    assert.ok(sucessoFoiMostrado(), "Deve mostrar overlay de sucesso");

    // 2. Fluxo de Sucesso Parcial
    resetMocks();
    _jobResultMock = { ok: true, hardware: { status: "parcial" } };
    await btn.onclick();
    assert.ok(!global.inicioLoaded, "Não deve chamar inicio.load no hardware.js");
    assert.ok(sucessoFoiMostrado(), "Deve mostrar overlay de sucesso"); // The finally block does esconderOverlay(true, true)

    // 3. Resposta sem job_id
    resetMocks();
    _forcarRescanMock = { return: { } }; // missing job_id
    await btn.onclick();
    assert.ok(!global.inicioLoaded, "Não deve carregar inicio se não houve job");
    assert.ok(erroFoiMostrado(), "Deve mostrar erro");

    // 4. Exceção da bridge
    resetMocks();
    _forcarRescanMock = { throw: "Timeout da bridge" };
    await btn.onclick();
    assert.ok(!global.inicioLoaded, "Não deve carregar inicio");
    assert.ok(erroFoiMostrado(), "Deve mostrar erro interno");
    assert.ok(!btn.disabled, "Botão deve continuar usável");

    // 5. jobResult null
    resetMocks();
    _jobResultMock = null;
    await btn.onclick();
    assert.ok(!global.inicioLoaded, "Não deve carregar inicio");
    assert.ok(erroFoiMostrado(), "Deve mostrar erro de falha");

    // 6. jobResult ok:false
    resetMocks();
    _jobResultMock = { ok: false, erro: "Ocorreu X" };
    await btn.onclick();
    assert.ok(!global.inicioLoaded, "Não deve recarregar página em caso de erro da job");
    assert.ok(erroFoiMostrado(), "Deve exibir msgErro no feedback");
    assert.ok(!btn.disabled, "Botão deve estar habilitado novamente");

    console.log("Testes do hardware.js passaram com sucesso.");
}

runTests().catch(e => {
    console.error("Falha no teste:", e);
    process.exit(1);
});
