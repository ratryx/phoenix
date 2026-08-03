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
      ui: {
          feedback: { mostrarOverlay: () => {}, esconderOverlay: () => {} },
          corPorPercentual: () => 'cor'
      },
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
        classList: { add: () => {}, remove: () => {} },
        appendChild: () => {},
        addEventListener: () => {}
      }),
      querySelectorAll: () => ([]),
      querySelector: () => null,
      createElement: (tag) => ({
        tag,
        style: {},
        dataset: {},
        className: "",
        classList: { add: () => {}, remove: () => {} },
        appendChild: () => {}
      })
    }
  },
  console: console
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
    let obter_inv_count = 0;
    sandbox.window.Phoenix.bridge.call = async (method) => {
      calls.push(method);
      if (method === "obter_inventario_atual") {
          obter_inv_count++;
          return obter_inv_count === 1 ? { status: "nao_carregado" } : { status: "completo", cpu: { modelo: "Intel" } };
      }
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
    console.log("Antes do carregarHardwareInicial");
    await sandbox.window.Phoenix.pages.inicio.carregarHardwareInicial();
    console.log("Depois do carregarHardwareInicial. hardware:", sandbox.window.Phoenix.state.hardware);
    assert(sandbox.window.Phoenix.state.hardware, "Estado hardware não populado");
    assert(calls.includes("carregar_hardware_cache"), "carregar_hardware_cache não chamado");

    let intervals = [];
    sandbox.window.Phoenix.lifecycle.setInterval = (name, fn, time) => {
      intervals.push({ name, time });
    };
    sandbox.window.Phoenix.pages.inicio.iniciarAtualizacaoTempoReal();
    assert(intervals.some(i => i.name === 'tempoRealInicio' && i.time === 3000), "Polling tempoReal não configurado corretamente");

    // 4. Teste Diagnóstico
    calls = [];
    await sandbox.window.Phoenix.pages.diagnostico.load();
    assert(calls.includes("obter_diagnostico"), "obter_diagnostico não chamado");

    // 5. Teste Hardware
    calls = [];
    await sandbox.window.Phoenix.pages.hardware.load();
    assert(calls.includes("obter_inventario_atual"), "obter_inventario_atual não chamado");

    console.log("Todos os testes JS readonly passaram.");
  } catch (e) {
    console.error("Testes falharam:", e);
    process.exit(1);
  }
}

runTests();
