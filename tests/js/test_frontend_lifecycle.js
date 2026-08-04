const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function loadScript(filePath, context) {
    const code = fs.readFileSync(path.resolve(__dirname, '../../', filePath), 'utf8');
    vm.runInContext(code, context);
}

// Map to store timer handles and callbacks
const activeTimers = new Map();
let nextTimerId = 1;

function fakeSetInterval(cb, delay) {
    const id = nextTimerId++;
    activeTimers.set(id, { cb, delay });
    return id;
}

function fakeClearInterval(id) {
    activeTimers.delete(id);
}

// Simulated Window
const windowObj = {
    location: { hash: '' },
    addEventListener: () => {},
                appendChild: () => {},
                removeChild: () => {},
    removeEventListener: () => {},
                appendChild: () => {},
                removeChild: () => {},
    setInterval: fakeSetInterval,
    clearInterval: fakeClearInterval
};

// Simulated DOM Elements
class MockElement {
    constructor(tag, id = null) {
        this.tag = tag;
        this.id = id;
        this.style = {};
        this._classes = new Set();
        this.textContent = '';
        this.innerHTML = '';
        this.dataset = {};
        this.disabled = false;
        this.children = [];
        this.listeners = {};
    }

    get classList() {
        const self = this;
        return {
            add: (c) => self._classes.add(c),
            remove: (c) => self._classes.delete(c),
            contains: (c) => self._classes.has(c)
        };
    }

    get className() {
        return Array.from(this._classes).join(' ');
    }

    set className(val) {
        this._classes = new Set(val.split(' ').filter(Boolean));
    }

    appendChild(child) {
        this.children.push(child);
        return child;
    }

    addEventListener(event, cb) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(cb);
    }

    removeEventListener(event, cb) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(l => l !== cb);
        }
    }

    dispatchEvent(event) {
        if (this.listeners[event.type]) {
            for (let cb of this.listeners[event.type]) {
                cb(event);
            }
        }
    }

    querySelector(sel) {
        if (sel === '.valor') {
            if (!this._valorEl) this._valorEl = new MockElement('span');
            return this._valorEl;
        }
        if (sel === '.gpu-metrics-container') {
            if (!this._gpuMetricsEl) {
                this._gpuMetricsEl = new MockElement('div');
                this._gpuMetricsEl.appendChild(new MockElement('div')); // child for progress bar usage if needed
            }
            return this._gpuMetricsEl;
        }
        if (sel === '.card-title') {
            if (!this._cardTitleEl) this._cardTitleEl = new MockElement('h2');
            return this._cardTitleEl;
        }
        return new MockElement('div');
    }
}

const mockDoc = {
    elements: {},
    getElementById: function(id) {
        if (!this.elements[id]) {
            this.elements[id] = new MockElement('div', id);
        }
        return this.elements[id];
    },
    querySelector: function(sel) {
        if (sel === '[data-card="gpu-uso"]') {
            if (!this.gpuCard) this.gpuCard = new MockElement('div');
            return this.gpuCard;
        }
        if (sel === '[data-card="cpu"]') {
            if (!this.cpuCard) this.cpuCard = new MockElement('div');
            return this.cpuCard;
        }
        if (sel === '[data-card="ram"]') {
            if (!this.ramCard) this.ramCard = new MockElement('div');
            return this.ramCard;
        }
        return new MockElement('div');
    },
    querySelectorAll: function() {
        return { forEach: (cb) => cb(new MockElement('div')) };
    },
    createElement: function(tag) {
        return new MockElement(tag);
    }
};

const callHistory = [];
const bridgeMock = {
    call: async (method) => {
        callHistory.push(method);
        return { ok: true };
    },
    whenReady: async () => {}
};

const context = vm.createContext({
    window: windowObj,
    document: mockDoc,
    setInterval: fakeSetInterval,
    clearInterval: fakeClearInterval,
    setTimeout: (cb) => { cb(); return 1; },
    clearTimeout: () => {},
    console: console,
    Number: Number,
    Math: Math,
    Promise: Promise,
    Array: Array
});

context.window.pywebview = { api: {} };

// Load Real Files
loadScript('gui/js/core/namespace.js', context);
loadScript('gui/js/core/state.js', context);
loadScript('gui/js/core/jobs.js', context);
loadScript('gui/js/core/bridge.js', context);
loadScript('gui/js/core/lifecycle.js', context);
loadScript('gui/js/core/router.js', context);
loadScript('gui/js/pages/inicio.js', context);
loadScript('gui/js/pages/hardware.js', context);

// Mock bridge implementation after namespace is initialized
context.window.Phoenix.bridge = bridgeMock;
context.window.Phoenix.ui = {
    corPorPercentual: () => 'cor',
    visualEffects: { initialize: async () => {}, refresh: () => {} },
    windowControls: { initialize: () => {} },
    feedback: { mostrarOverlay: () => {}, esconderOverlay: () => {}, atualizarOverlay: () => {} }
};

loadScript('gui/js/pages/inicio.js', context);
loadScript('gui/js/pages/hardware.js', context);
loadScript('gui/js/pages/sensores.js', context);

async function runTests() {
    console.log("=== Testando Lifecycle do Inicio (Real DOM + Harness) ===");
    const P = context.window.Phoenix;

    P.router.setPageLoader((id) => {
        if (P.pages[id] && typeof P.pages[id].load === 'function') {
            P.pages[id].load();
        }
    });

    P.state.hardware = { capacidades: { metricas_gpu_disponiveis: true } };

    // Helper para achar o callback da Início
    function getInicioTimerCb() {
        for (let [id, t] of activeTimers.entries()) {
            if (t.cb.name === '_atualizandoTempoReal' || t.cb === P.pages.inicio._atualizandoTempoReal || String(t.cb).includes('obter_metricas_rapidas')) {
                return t.cb;
            }
        }
        return null;
    }

    // 1. entrar na Início cria um timer
    activeTimers.clear();
    P.router.navigate("inicio");
    assert(activeTimers.size > 0, "Nenhum timer criado ao entrar na Início");
    let cb = getInicioTimerCb();
    assert(cb, "Callback de Início não encontrado");

    // 2. sair remove o timer
    P.router.navigate("hardware");
    assert(activeTimers.size === 0, "Timer não foi limpo ao sair");

    // 3. retornar cria exatamente um timer
    P.router.navigate("inicio");
    assert(activeTimers.size === 1, "Múltiplos ou nenhum timer criados ao retornar");
    cb = getInicioTimerCb();

    // 4. Promise pendente iniciada antes de sair é descartada (não suja o DOM)
    let resolveRapida;
    P.bridge.call = (method) => {
        if (method === "obter_metricas_rapidas") return new Promise(r => resolveRapida = r);
        if (method === "obter_gpu_rapida") return Promise.resolve({ ok: true, gpu: { nome: 'G', uso_percentual: 50, temperatura_c: 50 } });
        if (method === "obter_inventario_atual") return Promise.resolve({ status: "completo", cpu: { modelo: "X" } });
        return Promise.resolve({ ok: true });
    };

    // Zera o DOM
    const cpuValMock = mockDoc.querySelector('[data-card="cpu"]').querySelector('.valor');
    cpuValMock.textContent = 'Z';

    let updatePromise = cb(); // Dispara atualização, fica pendente em obter_metricas_rapidas

    // Sai da página, reqId é incrementado
    P.router.navigate("hardware");

    // Resolve a resposta atrasada
    resolveRapida({ ok: true, cpu_percent: 50.0 });
    await updatePromise;

    // O DOM não pode ter sido tocado
    assert(cpuValMock.textContent === 'Z', "DOM modificado por resposta órfã (promessa antiga)");
    assert(P.pages.inicio._atualizandoTempoReal === false, "Flag não foi resetada");

    // 5. Teste de requisição antiga concorrendo com requisição nova
    P.router.navigate("inicio");

    let resolveRapida1, resolveRapida2;
    let callCount = 0;
    P.bridge.call = (method) => {
        if (method === "obter_metricas_rapidas") {
            callCount++;
            if (callCount === 1) return new Promise(r => resolveRapida1 = r);
            if (callCount === 2) return new Promise(r => resolveRapida2 = r);
        }
        if (method === "obter_gpu_rapida") return Promise.resolve({ ok: true, gpu: { nome: 'G', uso_percentual: 10, temperatura_c: 10 } });
        if (method === "obter_inventario_atual") return Promise.resolve({ status: "completo", cpu: { modelo: "X" } });
        return Promise.resolve({ ok: true });
    };

    let p1 = getInicioTimerCb()(); // reqId atual, fica pendente em resolveRapida1

    // Incrementamos o _reqId para fingir que a página recarregou ou saiu e voltou
    P.router.navigate("hardware");
    P.router.navigate("inicio");

    let p2 = getInicioTimerCb()(); // Novo polling, fica pendente em resolveRapida2

    // P2 resolve primeiro
    resolveRapida2({ ok: true, cpu_percent: 80.0, ram_percent: 80.0 });
    await p2;
    // P2 resolve primeiro
    resolveRapida2({ ok: true, cpu_percent: 80.0, ram_percent: 80.0 });
    await p2;
    // O DOM deve refletir p2
    assert(String(cpuValMock.textContent) === '80', "DOM não refletiu a requisição nova");

    // P1 resolve depois (resposta órfã)
    resolveRapida1({ ok: true, cpu_percent: 10.0, ram_percent: 10.0 });
    await p1;
    // O DOM deve CONTINUAR refletindo p2, p1 foi ignorado
    assert(String(cpuValMock.textContent) === '80', "A requisição velha sobrescreveu o DOM da nova!");

    // 6. Confirma que rescan não cria polling da Início
    activeTimers.clear();
    P.router.navigate("hardware");

    // Prepara botão de rescan
    const btnRescan = mockDoc.getElementById('btn-atualizar-hardware');

    let rescanCalled = false;
    const origBridgeCall = P.bridge.call;
    P.bridge.call = (method) => {
        if (method === "forcar_rescan_hardware") {
            rescanCalled = true;
            return Promise.resolve({ job_id: '123' });
        }
        return origBridgeCall(method);
    };

    // Para evitar que job falhe, mockamos jobs.awaitJob
    P.jobs = { awaitJob: async (id, cb) => { cb(100, "Concluído"); return { ok: true }; } };

    // Simula o clique do usuário no botão que dispara o listener de rescan
    // O evento de clique é adicionado no hardware.load()
    await P.pages.hardware.load();
    btnRescan.dispatchEvent({ type: 'click' });

    // Aguarda microtasks
    await new Promise(r => setTimeout(r, 0));

    // Verifica
    assert(rescanCalled, "O listener do botão rescan não chamou forcar_rescan_hardware");
    assert(getInicioTimerCb() === null, "Polling de Início foi criado indevidamente durante o rescan em Hardware");

    P.bridge.call = origBridgeCall;

    console.log("Todos os testes JS de lifecycle (DOM real+Map timers) passaram.");
}

runTests().catch(err => {
    console.error(err);
    process.exit(1);
});
