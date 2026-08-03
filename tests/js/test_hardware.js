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
                addEventListener: function(evt, cb) {
                    this['on' + evt] = cb;
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
        return { tag, style: {}, classList: { add: () => {} }, appendChild: () => {} };
    }
};

// Mock Phoenix
global.window = {};
global.Phoenix = {
    bridge: {
        call: async (method) => {
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
                return { job_id: "job-123" };
            }
        }
    },
    jobs: {
        awaitJob: async (jobId) => {
            return {
                ok: true,
                resultado: {
                    hardware: { status: "completo" }
                }
            };
        },
        waitFor: async (jobId) => {
            throw new Error("PROIBIDO: waitFor não deve ser usado no hardware.js");
        }
    },
    state: {},
    ui: {
        feedback: {
            mostrarProcessando: () => {},
            esconderOverlay: () => {},
            mostrarSucesso: () => {},
            mostrarAviso: () => {},
            mostrarErro: () => {}
        },
        visualEffects: {
            refresh: () => {
                global.visualEffectsRefreshed = true;
            }
        }
    },
    pages: {
        inicio: {
            load: () => {
                global.inicioLoaded = true;
            }
        }
    }
};

global.window.Phoenix = global.Phoenix;

// Load hardware.js
require('../../gui/js/pages/hardware.js');

async function runTests() {
    console.log("Rodando testes test_hardware.js...");
    
    // Testa o load inicial
    await Phoenix.pages.hardware.load();
    const btn = document.getElementById('btn-atualizar-hardware');
    assert.ok(btn.onclick !== null || btn.dataset.ev === "1");
    
    // Reseta estado mock
    global.visualEffectsRefreshed = false;
    global.inicioLoaded = false;
    
    // Simula clique no botão atualizar
    if (btn.onclick) await btn.onclick();
    
    assert.ok(global.inicioLoaded, "inicio.load() deveria ter sido chamado");
    assert.ok(global.visualEffectsRefreshed, "visualEffects.refresh() deveria ter sido chamado");
    
    console.log("Testes do hardware.js passaram com sucesso.");
}

runTests().catch(e => {
    console.error("Falha no teste:", e);
    process.exit(1);
});
