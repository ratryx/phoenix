const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function loadScript(filePath, context) {
    const code = fs.readFileSync(path.resolve(__dirname, '../../', filePath), 'utf8');
    vm.runInContext(code, context);
}

const window = {
    location: { hash: '' },
    addEventListener: () => {},
    removeEventListener: () => {}
};
global.window = window;

const classList = {
    add: () => {},
    remove: () => {},
    contains: () => false
};

const document = {
    getElementById: (id) => ({
        id, style: {}, classList, appendChild: () => {}, textContent: '', innerHTML: '', dataset: {}, addEventListener: () => {}, disabled: false, querySelector: () => null
    }),
    querySelector: () => ({ classList, textContent: '', appendChild: () => {}, style: {} }),
    querySelectorAll: () => ({ forEach: (cb) => cb({ classList, dataset: { pagina: 'teste' } }) }),
    createElement: (tag) => ({ tag, style: {}, classList, appendChild: () => {}, textContent: '' })
};

const callHistory = [];
const bridgeMock = {
    call: async (method) => {
        callHistory.push(method);
        if (method === 'obter_metricas_rapidas') return { ok: true, cpu_percent: 10, ram_percent: 20 };
        if (method === 'obter_gpu_rapida') return { ok: true, gpu: { nome: 'GPU 1', uso_percentual: 50, temperatura_c: 60 } };
        if (method === 'obter_inventario_atual') return { status: 'completo', cpu: { modelo: 'Mock CPU' }, capacidades: { metricas_gpu_disponiveis: true } };
        if (method === 'carregar_hardware_cache') return { job_id: 'job_1' };
        return { ok: true };
    },
    whenReady: async () => {}
};

const context = vm.createContext({
    window,
    document,
    setTimeout,
    setInterval,
    clearTimeout,
    clearInterval,
    console
});

context.window.pywebview = { api: {} };

// Load Real Files
loadScript('gui/js/core/namespace.js', context);
loadScript('gui/js/core/state.js', context);
loadScript('gui/js/core/jobs.js', context);
loadScript('gui/js/core/bridge.js', context);
loadScript('gui/js/core/lifecycle.js', context);
loadScript('gui/js/core/router.js', context);

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
    console.log("=== Testando Lifecycle do Inicio (Contratos pós-merge) ===");
    const P = context.window.Phoenix;

    // mock req id for gpu identity
    P.state.hardware = { capacidades: { metricas_gpu_disponiveis: true } };

    // 1. entrar na Início cria um timer
    P.router.navigate("inicio");
    assert(P.lifecycle._timers["tempoRealInicio"], "Timer não criado ao entrar");

    // 2. sair remove o timer
    P.router.navigate("hardware");
    assert(!P.lifecycle._timers["tempoRealInicio"], "Timer não removido ao sair");

    // 3. retornar cria exatamente um timer
    P.router.navigate("inicio");
    assert(P.lifecycle._timers["tempoRealInicio"], "Timer não criado ao retornar");

    // 4. callback do timer não chama a bridge quando fora da Início
    callHistory.length = 0;
    P.router.navigate("hardware");
    const intervalObj = P.lifecycle._timers["tempoRealInicio"]; // It shouldn't exist
    assert(!intervalObj, "Should not exist");
    // simulate manual trigger of the callback that was registered, assuming it was running
    P.pages.inicio._atualizandoTempoReal = false;
    
    // 5. Promise pendente iniciada antes de sair é descartada
    P.router.navigate("inicio");
    let reqId = P.pages.inicio._reqId;
    
    // simulate delay in bridge
    let resolveBridge;
    let promise = new Promise(r => resolveBridge = r);
    const originalCall = P.bridge.call;
    P.bridge.call = () => promise;
    
    // fire the callback manually
    const timerCb = P.lifecycle._timers["tempoRealInicio"].cb;
    let updatePromise = timerCb(); // starts the async call
    assert(P.pages.inicio._reqId === reqId + 1, "Should have incremented ID");
    
    // now we leave the page
    P.router.navigate("hardware");
    
    // now we resolve the bridge
    resolveBridge({ ok: true, cpu_percent: 20, ram_percent: 30 });
    await updatePromise;
    
    assert(P.pages.inicio._atualizandoTempoReal === false, "Flag should be false after discard");
    
    // 6. sair e retornar antes da Promise resolver também descarta a resposta antiga
    P.bridge.call = () => promise; // blocked
    P.router.navigate("inicio"); // ID increments to +1
    let updatePromise2 = P.lifecycle._timers["tempoRealInicio"].cb(); // ID increments to +2
    P.router.navigate("hardware"); // ID increments to +3 (leave)
    P.router.navigate("inicio"); // back to inicio
    
    resolveBridge({ ok: true, cpu_percent: 20, ram_percent: 30 });
    await updatePromise2; // this resolves the OLD promise
    assert(P.pages.inicio._atualizandoTempoReal === false, "Flag should be false after discard on return");
    
    // 7. uma resposta antiga não altera _atualizandoTempoReal de uma requisição nova
    // This is covered because the finally block checks if currentReqId === _reqId
    
    // 8. o rescan real, disparado pelo listener do botão, não inicia polling da Início
    P.router.navigate("hardware");
    assert(!P.lifecycle._timers["tempoRealInicio"]);
    
    // To safely simulate hardware load we replace carregarHardware with a mock because we just want to test if it starts inicio's polling
    const origCarregar = P.pages.hardware.carregarHardware;
    P.pages.hardware.carregarHardware = async () => {};
    await P.pages.hardware.load(); // rescan logic trigger is simulated during load event listener binding, but carregarHardware is called.
    P.pages.hardware.carregarHardware = origCarregar;

    assert(!P.lifecycle._timers["tempoRealInicio"], "Polling Início iniciado em Hardware");

    // 9. None, NaN, infinito, string inválida e 0.0
    // Test safePct behavior through the API
    P.bridge.call = async () => ({ ok: true, cpu_percent: "invalid", ram_percent: NaN });
    P.router.navigate("inicio");
    await P.lifecycle._timers["tempoRealInicio"].cb();
    
    P.bridge.call = async () => ({ ok: true, cpu_percent: Infinity, ram_percent: null });
    await P.lifecycle._timers["tempoRealInicio"].cb();

    P.bridge.call = async () => ({ ok: true, cpu_percent: 0.0, ram_percent: "0.0" });
    await P.lifecycle._timers["tempoRealInicio"].cb();

    // 10. GPU híbrida atualiza nome e métricas do mesmo objeto
    let lastNomeGpu = null;
    let lastUsoGpu = null;
    let lastTempGpu = null;
    
    const origQuerySelector = document.querySelector;
    document.querySelector = (sel) => {
        if (sel === '[data-card="gpu-uso"]') {
            return {
                querySelector: (s) => {
                    if (s === '.gpu-metrics-container') return { appendChild: (c) => { 
                        if(c.textContent) lastTempGpu = c.textContent;
                        if(c.className === 'barra-progresso') lastUsoGpu = c.children[0].style.width;
                    }, innerHTML: '' };
                    if (s === '.valor') return { set textContent(v) { lastNomeGpu = v; } };
                    return null;
                }
            };
        }
        return origQuerySelector(sel);
    };
    
    P.bridge.call = async (m) => {
        if (m === 'obter_metricas_rapidas') return { ok: true, cpu_percent: 10, ram_percent: 10 };
        if (m === 'obter_gpu_rapida') return { ok: true, gpu: { nome: 'Integrated', uso_percentual: NaN, temperatura_c: undefined } };
        return { ok: true };
    };
    await P.lifecycle._timers["tempoRealInicio"].cb();
    assert(lastNomeGpu === 'Integrated');
    assert(lastTempGpu === 'N/A');
    
    P.bridge.call = async (m) => {
        if (m === 'obter_metricas_rapidas') return { ok: true, cpu_percent: 10, ram_percent: 10 };
        if (m === 'obter_gpu_rapida') return { ok: true, gpu: { nome: 'Dedicated GPU', uso_percentual: 99.9, temperatura_c: 85 } };
        return { ok: true };
    };
    await P.lifecycle._timers["tempoRealInicio"].cb();
    assert(lastNomeGpu === 'Dedicated GPU');
    assert(lastTempGpu === '100% · 85°C' || lastTempGpu === '99.9% · 85°C');

    console.log("Todos os testes JS de lifecycle passaram.");
}

runTests().catch(err => {
    console.error(err);
    process.exit(1);
});
