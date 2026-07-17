const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

// Criar ambiente simulado
const sandbox = {
  window: {
    Phoenix: {
      bridge: { call: async () => ({ ok: true }) },
      lifecycle: { setInterval: () => {} },
      ui: { feedback: { mostrarOverlay: () => {}, esconderOverlay: () => {} } },
      jobs: { awaitJob: async () => ({ ok: true }) },
      state: {},
      pages: {}
    },
    document: {
      getElementById: () => ({
        textContent: '',
        style: { display: '' },
        innerHTML: '',
        dataset: {},
        classList: { add: () => {}, remove: () => {} }
      }),
      querySelectorAll: () => ([]),
      querySelector: () => null
    }
  },
  console: { error: () => {}, log: () => {} }
};

// Configurar referências circulares e globais
sandbox.window.document.window = sandbox.window;
sandbox.Phoenix = sandbox.window.Phoenix;
sandbox.document = sandbox.window.document;

vm.createContext(sandbox);

function loadModule(filePath) {
  const code = fs.readFileSync(path.resolve(__dirname, '../../', filePath), 'utf8');
  vm.runInContext(code, sandbox);
}

// Carregar modules
try {
  loadModule('gui/js/pages/inicio.js');
  loadModule('gui/js/pages/diagnostico.js');
  loadModule('gui/js/pages/hardware.js');
} catch (e) {
  console.error("Falha ao carregar módulos:", e);
  process.exit(1);
}

// ---------------------------------------------------------
// Testes
// ---------------------------------------------------------

async function runTests() {
  try {
    // 1. Módulos Registrados
    assert(sandbox.window.Phoenix.pages.inicio, "Módulo inicio não registrado");
    assert(sandbox.window.Phoenix.pages.diagnostico, "Módulo diagnostico não registrado");
    assert(sandbox.window.Phoenix.pages.hardware, "Módulo hardware não registrado");

    // 2. Mock Bridge calls
    let calls = [];
    sandbox.window.Phoenix.bridge.call = async (method) => {
      calls.push(method);
      if (method === "carregar_hardware_cache") return { job_id: "hw_job" };
      if (method === "obter_diagnostico") return { job_id: "diag_job" };
      if (method === "obter_info_sistema_detalhado") return { ok: true, cpu: {}, ram: {}, sistema: {}, discos: [] };
      return { ok: true };
    };
    sandbox.window.Phoenix.jobs.awaitJob = async (job_id) => {
      if (job_id === "hw_job") return { ok: true, hardware: { cpu: {}, ram: {}, gpus: [] } };
      if (job_id === "diag_job") return { ok: true, dados: { cpu: {}, memoria: {}, discos: [], processos: [] } };
      return { ok: true };
    };

    // 3. Teste Início
    await sandbox.window.Phoenix.pages.inicio.carregarHardwareInicial();
    assert(sandbox.window.Phoenix.state.hardware, "Estado hardware não populado");
    assert(calls.includes("carregar_hardware_cache"), "carregar_hardware_cache não chamado");

    let intervals = [];
    sandbox.window.Phoenix.lifecycle.setInterval = (name, fn, time) => {
      intervals.push({ name, time });
    };
    sandbox.window.Phoenix.pages.inicio.iniciarAtualizacaoTempoReal();
    assert(intervals.some(i => i.name === 'tempoReal' && i.time === 3000), "Polling tempoReal não configurado corretamente");

    // 4. Teste Diagnóstico
    calls = [];
    await sandbox.window.Phoenix.pages.diagnostico.load();
    assert(calls.includes("obter_diagnostico"), "obter_diagnostico não chamado");

    // 5. Teste Hardware
    calls = [];
    await sandbox.window.Phoenix.pages.hardware.load();
    assert(calls.includes("obter_info_sistema_detalhado"), "obter_info_sistema_detalhado não chamado");
    assert(sandbox.window.Phoenix.state.dadosSistema, "Estado dadosSistema não populado");

    console.log("Todos os testes JS readonly passaram.");
  } catch (e) {
    console.error("Testes falharam:", e);
    process.exit(1);
  }
}

runTests();
