const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

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
        getElementById: (id) => {
          if (!sandbox.domElements[id]) {
            sandbox.domElements[id] = {
              id, textContent: '', style: { display: '', width: '' }, innerHTML: '', dataset: {}, children: [],
              classList: { add: () => {}, remove: () => {} },
              appendChild: function(c) {
                this.children.push(c);
              }
            };
          }
          return sandbox.domElements[id];
        },
        createElement: (tag) => {
          const el = {
            tag, style: {}, classList: { add: () => {}, remove: () => {} }, dataset: {}, children: [],
            appendChild: function(c) {
              this.children.push(c);
            }
          };
          Object.defineProperty(el, 'id', {
            set: function(val) {
              this._id = val;
              sandbox.domElements[val] = this;
            },
            get: function() { return this._id; }
          });
          return el;
        }
      }
    },
    console: { error: (e, ex) => { console.error("PAGE ERROR", e, ex); }, log: () => {} },
    intervals: [],
    setTimeout: setTimeout,
    clearTimeout: clearTimeout,
    domElements: {}
  };

  sandbox.document = sandbox.window.document;
  sandbox.Phoenix = sandbox.window.Phoenix;
  vm.createContext(sandbox);
  const code = fs.readFileSync(path.resolve(__dirname, '../../gui/js/pages/sensores.js'), 'utf8');
  vm.runInContext(code, sandbox);

  try {
    const page = sandbox.window.Phoenix.pages.hwmonitor;
    assert(page, "Módulo não registrado como Phoenix.pages.hwmonitor");

    // Mock initial bridge
    let nextResult = {};
    sandbox.Phoenix.bridge.call = async (method) => {
      if (method === "obter_metricas_completas") return nextResult;
      return { ok: true };
    };

    await page.load();
    while (sandbox.window.Phoenix.pages.hwmonitor.isUpdatingForTests()) {
       await new Promise(r => setTimeout(r, 10)); // wait for first load to settle
    }
    const gpusCont = sandbox.document.getElementById('hw-gpus-container');

    // 1. Success complete V2 with multiples GPUs
    nextResult = {
      ok: true,
      cpu: { uso_percentual: 50, uso_por_nucleo: [10, 20], frequencia_atual_mhz: 3000 },
      memoria: { percentual_uso: 40, usada_gb: 8, disponivel_gb: 8 },
      disco: { leitura_mb_s: 10, escrita_mb_s: 20 },
      gpus: [
        { id: "gpu1", uso_percentual: 30, temperatura_c: 60, vram_usada_mb: 1024, vram_total_mb: 2048 },
        { id: "gpu2", uso_percentual: 10, temperatura_c: 40, vram_usada_mb: 512, vram_total_mb: 2048 }
      ]
    };
    await page.atualizar();

    // ID Stable checking
    const gpu1Title = sandbox.document.getElementById('gpu-card-gpu1');
    assert.ok(gpu1Title, "GPU 1 deve ser criada");
    const gpu2Title = sandbox.document.getElementById('gpu-card-gpu2');
    assert.ok(gpu2Title, "GPU 2 deve ser criada");
    const gpu1Vram = sandbox.document.getElementById('gpu-vram-gpu1');
    assert.strictEqual(gpu1Vram.textContent, "1024 / 2048 MB");

    // Store reference to check if it's rebuilt
    const initialGpu1 = gpu1Title;

    // 2. Clamp values and missing VRAM/freq
    nextResult = {
      ok: true,
      cpu: { uso_percentual: 150, frequencia_atual_mhz: null }, // clamp to 100, N/A
      memoria: { percentual_uso: -10, usada_gb: NaN },          // clamp to 0, N/A
      gpus: [
        { id: "gpu1", uso_percentual: undefined, temperatura_c: -5, vram_usada_mb: null, vram_total_mb: undefined },
        { id: "gpu2", uso_percentual: 10, temperatura_c: 40, vram_usada_mb: 512, vram_total_mb: 2048 }
      ]
    };
    await page.atualizar();
    assert.strictEqual(sandbox.document.getElementById('hw-cpu-total').textContent, 100);
    assert.strictEqual(sandbox.document.getElementById('hw-cpu-freq').textContent, "N/A");
    assert.strictEqual(sandbox.document.getElementById('hw-ram-pct').textContent, 0);
    assert.strictEqual(sandbox.document.getElementById('hw-ram-usada').textContent, "N/A");
    assert.strictEqual(sandbox.document.getElementById('gpu-vram-gpu1').textContent, "N/A");
    assert.strictEqual(sandbox.document.getElementById('gpu-temp-gpu1').textContent, "N/A");
    assert.strictEqual(sandbox.document.getElementById('gpu-uso-gpu1').textContent, "N/A");

    const gpu1TitleAgain = sandbox.document.getElementById('gpu-card-gpu1');
    assert.strictEqual(initialGpu1, gpu1TitleAgain, "Card não deveria ser recriado se IDs não mudaram");

    // 3. GPU removed
    nextResult = {
      ok: true,
      cpu: { uso_percentual: 50 },
      gpus: [
        { id: "gpu1", uso_percentual: 30 }
      ]
    };
    await page.atualizar();
    assert.strictEqual(gpusCont.innerHTML, '', "Deve refazer a árvore de GPUs se a lista de IDs mudou");

    // 4. Parcial missing GPU or CPU
    nextResult = {
      ok: true,
      memoria: { percentual_uso: 55 }
      // CPU and GPU and disk are missing completely
    };
    await page.atualizar();
    assert.strictEqual(sandbox.document.getElementById('hw-ram-pct').textContent, 55, "Deve preservar e atualizar apenas o que está presente");

    // 5. Test page.leave during async
    let resolveBridge;
    sandbox.Phoenix.bridge.call = () => {
      return new Promise(r => resolveBridge = r);
    };
    let updatePromise = page.atualizar();
    page.leave();
    resolveBridge({ ok: true, cpu: { uso_percentual: 88 } });
    await updatePromise;
    assert.notStrictEqual(sandbox.document.getElementById('hw-cpu-total').textContent, 88, "Não deve atualizar UI se leave() foi chamado durante a call");

    // Ensure "undefined" text does not exist anywhere in domElements mock text contents
    for (let key in sandbox.domElements) {
      if (typeof sandbox.domElements[key].textContent === 'string') {
         assert.ok(!sandbox.domElements[key].textContent.includes("undefined"), `undefined text in ${key}`);
         assert.ok(!sandbox.domElements[key].textContent.includes("NaN"), `NaN text in ${key}`);
         assert.ok(!sandbox.domElements[key].textContent.includes("null"), `null text in ${key}`);
      }
    }

    console.log("Todos os testes de sensores JS passaram.");
  } catch(e) {
    console.error(e);
    process.exit(1);
  }
}

runAsyncTests();
