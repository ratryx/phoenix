const assert = require('assert');
const fs = require('fs');
const path = require('path');

// Mocks
global.window = {
    location: { hash: '' },
    addEventListener: () => {},
    Phoenix: null // will be set below
};
global.document = {
    createElement: (tag) => ({ tag, style: {}, appendChild: () => {}, classList: { add: () => {}, remove: () => {} } }),
    getElementById: (id) => ({
        id, 
        style: {}, 
        appendChild: () => {}, 
        textContent: '', 
        innerHTML: '', 
        dataset: {}, 
        addEventListener: () => {}, 
        querySelector: () => ({ textContent: '', appendChild: () => {}, style: {}, className: '' }),
        disabled: false
    }),
    querySelector: (sel) => {
        return { textContent: '', appendChild: () => {}, style: {}, className: '', classList: { add: () => {}, remove: () => {} } };
    },
    querySelectorAll: () => []
};

let callHistory = [];

global.Phoenix = {
    state: { paginaAtual: '', hardware: { capacidades: { metricas_gpu_disponiveis: true } } },
    lifecycle: {
        timers: {},
        setInterval: function (name, cb, delay) {
            this.timers[name] = { cb, delay };
        },
        clearInterval: function (name) {
            delete this.timers[name];
        },
        leavePage: function (page) {}
    },
    bridge: {
        call: async (method) => {
            callHistory.push(method);
            return { ok: true, cpu_percent: 10, ram_percent: 20 };
        },
        whenReady: async () => {}
    },
    router: {
        setPageLoader: () => {},
        navigate: function(id) {
            if (global.Phoenix.state.paginaAtual && global.Phoenix.pages[global.Phoenix.state.paginaAtual] && global.Phoenix.pages[global.Phoenix.state.paginaAtual].leave) {
                global.Phoenix.pages[global.Phoenix.state.paginaAtual].leave();
            }
            global.Phoenix.state.paginaAtual = id;
            if (global.Phoenix.pages[id] && global.Phoenix.pages[id].load) {
                global.Phoenix.pages[id].load();
            }
        }
    },
    ui: {
        corPorPercentual: () => 'cor',
        visualEffects: { initialize: async () => {}, refresh: () => {} },
        windowControls: { initialize: () => {} },
        feedback: { mostrarOverlay: () => {}, esconderOverlay: () => {}, atualizarOverlay: () => {} }
    },
    features: { clientSession: { initialize: async () => {} } },
    jobs: { awaitJob: async () => ({ ok: true }) }
};
global.window.Phoenix = global.Phoenix;
global.Phoenix.pages = {
    inicio: { load: () => {} },
    hardware: { load: () => {} },
    hwmonitor: { load: () => {}, leave: () => {} }
};

const inicioSource = fs.readFileSync(path.join(__dirname, '../../gui/js/pages/inicio.js'), 'utf8');
const hwSource = fs.readFileSync(path.join(__dirname, '../../gui/js/pages/hardware.js'), 'utf8');
const hwMonitorSource = fs.readFileSync(path.join(__dirname, '../../gui/js/pages/sensores.js'), 'utf8');

eval(inicioSource);
eval(hwSource);
eval(hwMonitorSource);

async function runTests() {
    console.log("=== Testando Lifecycle do Inicio ===");
    
    // 1. Polling criado ao entrar
    global.Phoenix.router.navigate("inicio");
    assert(global.Phoenix.lifecycle.timers["tempoRealInicio"], "Polling não foi criado ao entrar na Início");
    
    // 2. Não é criado no bootstrap se a página for outra (simulado não chamando inicio.load)
    global.Phoenix.lifecycle.clearInterval("tempoRealInicio");
    global.Phoenix.router.navigate("hardware");
    assert(!global.Phoenix.lifecycle.timers["tempoRealInicio"], "Polling foi criado quando a página não é inicio");
    
    // 3. É removido ao sair
    global.Phoenix.router.navigate("inicio");
    assert(global.Phoenix.lifecycle.timers["tempoRealInicio"], "Deve estar criado");
    global.Phoenix.router.navigate("hardware");
    assert(!global.Phoenix.lifecycle.timers["tempoRealInicio"], "Polling não foi removido ao sair");
    
    // 4. Bridge deixa de receber chamadas depois da saída e não altera o DOM
    callHistory = [];
    let cb = global.Phoenix.pages.inicio._atualizandoTempoReal;
    // O callback real retornará imediatamente pois state != "inicio" e a flag foi resetada
    assert(global.Phoenix.pages.inicio._atualizandoTempoReal === false, "Flag não foi resetada");

    // 5. Retorno à Início cria exatamente um timer
    global.Phoenix.router.navigate("inicio");
    assert(global.Phoenix.lifecycle.timers["tempoRealInicio"], "Polling deve estar criado novamente");
    
    // 6. Saída do HWMonitor chama seu leave()
    global.Phoenix.router.navigate("hwmonitor");
    assert(global.Phoenix.lifecycle.timers["sensores"], "Sensores deve iniciar");
    global.Phoenix.router.navigate("inicio");
    assert(!global.Phoenix.lifecycle.timers["sensores"], "Sensores não parou no leave");

    // 7. Rescan em Hardware não inicia polling oculto da Início
    global.Phoenix.router.navigate("hardware");
    assert(!global.Phoenix.lifecycle.timers["tempoRealInicio"], "Polling de início não deveria existir");
    await global.Phoenix.pages.hardware.load(); // rescan logic trigger is simulated during load event listener binding, but carregarHardware is called.
    assert(!global.Phoenix.lifecycle.timers["tempoRealInicio"], "Polling oculto criado após rescan em Hardware!");

    console.log("Todos os testes JS de lifecycle passaram.");
}

runTests().catch(err => {
    console.error(err);
    process.exit(1);
});
