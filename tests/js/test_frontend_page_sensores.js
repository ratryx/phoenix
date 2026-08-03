const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

function runTests() {
  const sandbox = {
    window: {
      Phoenix: {
        bridge: { call: async () => ({ ok: true }) },
        lifecycle: {
          setInterval: (name, cb, t) => { sandbox.intervals.push({name, cb, t}); },
          clearInterval: (name) => { sandbox.intervals = sandbox.intervals.filter(i => i.name !== name); }
        },
        ui: { corPorPercentual: () => 'cor' },
        state: { hardware: { gpus: [] }, paginaAtual: 'hwmonitor' },
        pages: {}
      },
      document: {
        getElementById: (id) => ({
          textContent: '',
          style: { display: '', width: '' },
          innerHTML: '',
          dataset: {},
          classList: { add: () => {}, remove: () => {} }
        }),
        querySelectorAll: () => ([]),
        querySelector: () => null
      }
    },
    console: { error: () => {}, log: () => {} },
    intervals: [],
    setTimeout: setTimeout,
    clearTimeout: clearTimeout
  };

  sandbox.document = sandbox.window.document;
  sandbox.Phoenix = sandbox.window.Phoenix;

  vm.createContext(sandbox);

  const code = fs.readFileSync(path.resolve(__dirname, '../../gui/js/pages/sensores.js'), 'utf8');
  vm.runInContext(code, sandbox);

  // Tests
  try {
    const page = sandbox.window.Phoenix.pages.hwmonitor;
    assert(page, "Módulo não registrado como Phoenix.pages.hwmonitor");
    assert(sandbox.intervals.length === 0, "Arquivo não inicia polling ao ser carregado");

    // Mock bridge call
    let callCount = 0;
    sandbox.Phoenix.bridge.call = async (method) => {
      if (method === "obter_metricas_completas") callCount++;
      return {
        ok: true,
        cpu: { uso_percentual: 50, uso_por_nucleo: [10, 20], frequencia_atual_mhz: 3000 },
        memoria: { percentual_uso: 40, usada_gb: 8, disponivel_gb: 8 },
        gpus: [{ uso_percentual: 30, temperatura_c: 60, vram_usada_mb: 1024, vram_total_mb: 2048 }],
        disco: { leitura_mb_s: 10, escrita_mb_s: 20 }
      };
    };

    // Load
    sandbox.intervals = [];
    let initialCount = callCount;
    page.load(); // it's async but doesn't return promise in original design? Wait, load is async in my code.
    // Since load is async, let's wait a bit.

    // We can't await easily since it's just a test function without async context at top level.
    // I will wrap in async IIFE.
  } catch (e) {
    console.error(e);
    process.exit(1);
  }
}

async function runAsyncTests() {
  const sandbox = {
    window: {
      Phoenix: {
        bridge: { call: async () => ({ ok: true }) },
        lifecycle: {
          setInterval: (name, cb, t) => { sandbox.intervals.push({name, cb, t}); },
          clearInterval: (name) => { sandbox.intervals = sandbox.intervals.filter(i => i.name !== name); }
        },
        ui: { corPorPercentual: () => 'cor' },
        state: { hardware: { gpus: [] }, paginaAtual: 'hwmonitor' },
        pages: {}
      },
      document: {
        getElementById: (id) => ({
          textContent: '',
          style: { display: '', width: '' },
          innerHTML: '',
          dataset: {},
          classList: { add: () => {}, remove: () => {} },
          appendChild: () => {}
        }),
        querySelectorAll: () => ([]),
        querySelector: () => null,
        createElement: (tag) => ({ tag, style: {}, classList: { add: () => {}, remove: () => {} }, appendChild: () => {} })
      }
    },
    console: { error: () => {}, log: () => {} },
    intervals: [],
    setTimeout: setTimeout,
    clearTimeout: clearTimeout
  };

  sandbox.document = sandbox.window.document;
  sandbox.Phoenix = sandbox.window.Phoenix;

  vm.createContext(sandbox);

  const code = fs.readFileSync(path.resolve(__dirname, '../../gui/js/pages/sensores.js'), 'utf8');
  vm.runInContext(code, sandbox);

  try {
    const page = sandbox.window.Phoenix.pages.hwmonitor;
    assert(page, "Módulo não registrado como Phoenix.pages.hwmonitor");
    assert(sandbox.intervals.length === 0, "Arquivo não inicia polling ao ser carregado");

    let callCount = 0;
    sandbox.Phoenix.bridge.call = async (method) => {
      if (method === "obter_metricas_completas") {
        callCount++;
        // Simulate delay to test overlap
        await new Promise(r => setTimeout(r, 10));
      }
      return {
        ok: true,
        cpu: { uso_percentual: 50, uso_por_nucleo: [10, 20], frequencia_atual_mhz: 3000 },
        memoria: { percentual_uso: 40, usada_gb: 8, disponivel_gb: 8 },
        gpus: [{ uso_percentual: 30, temperatura_c: 60, vram_usada_mb: 1024, vram_total_mb: 2048 }],
        disco: { leitura_mb_s: 10, escrita_mb_s: 20 }
      };
    };

    // Load
    await page.load();
    await new Promise(r => setTimeout(r, 20)); // let initial atualizar finish
    assert(callCount === 1, "load() deve chamar obter_metricas_completas");
    assert(sandbox.intervals.some(i => i.name === 'sensores' && i.t === 3000), "Polling registrado com 3000 ms");

    // Concorrência
    let p1 = page.atualizar();
    let p2 = page.atualizar();
    await Promise.all([p1, p2]);
    await new Promise(r => setTimeout(r, 20)); // wait finish
    // The second call should abort because atualizando is true
    assert(callCount === 2, "duas atualizações simultâneas não chamam a bridge duas vezes");

    // Erros
    sandbox.Phoenix.bridge.call = async () => ({ ok: false });
    await page.atualizar(); // This should reset flag
    let p3 = page.atualizar();
    await p3;
    assert(callCount === 2, "Erro da bridge não deixa flag presa");

    // Lifecycle
    page.enter();
    page.enter(); // should clear first
    assert(sandbox.intervals.filter(i => i.name === 'sensores').length === 1, "entrar duas vezes não duplica timer");

    page.leave();
    assert(sandbox.intervals.length === 0, "sair remove timer");

    // Limits
    const codeStr = code.toString();
    assert(!codeStr.includes("executarLimpeza"), "módulo não contém ações de limpeza");
    assert(!codeStr.includes("executarOtimizacao"), "módulo não contém ações de otimização");
    assert(!codeStr.includes("carregarServicos"), "módulo não contém serviços");
    assert(!codeStr.includes("executarRotinaCompleta"), "módulo não contém rotina completa");
    assert(!codeStr.includes("_sensoresInterval"), "nenhum _sensoresInterval");
    assert(!codeStr.match(/(?<!lifecycle\.)setInterval\(/), "nenhum setInterval direto");
    assert(!codeStr.match(/(?<!lifecycle\.)clearInterval\(/), "nenhum clearInterval direto");

    console.log("Todos os testes de sensores JS passaram.");
  } catch(e) {
    console.error(e);
    process.exit(1);
  }
}

runAsyncTests();
