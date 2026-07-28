const fs = require('fs');
const vm = require('vm');

function runTest() {
    console.log("=== INICIANDO TESTES DO JOBS ===");

    const code = fs.readFileSync('gui/js/core/jobs.js', 'utf8');

    // Mocks
    const bridge = {
        call: async (method, ...args) => {
            if (method === "verificar_tarefa") {
                return bridge.mockVerificar(args[0]);
            }
            if (method === "cancelar_tarefa") {
                return bridge.mockCancelar(args[0]);
            }
        },
        mockVerificar: (id) => ({ status: "running" }),
        mockCancelar: (id) => ({ ok: true })
    };

    const Phoenix = {
        bridge: bridge,
        jobs: {}
    };

    const context = { 
        window: { Phoenix: Phoenix }, 
        Phoenix: Phoenix, 
        console: console, 
        setTimeout: setTimeout,
        clearTimeout: clearTimeout,
        AbortController: AbortController,
        Promise: Promise
    };
    vm.createContext(context);
    vm.runInContext(code, context);

    const jobs = Phoenix.jobs;
    let passed = 0;
    let failed = 0;

    function assertEq(a, b, msg) {
        if (a !== b) {
            console.error(`❌ [FALHA] ${msg}: esperado ${b}, obtido ${a}`);
            failed++;
        } else {
            console.log(`✅ [OK] ${msg}`);
            passed++;
        }
    }

    async function test_success() {
        bridge.mockVerificar = () => ({ status: "done", resultado: { ok: true, v: 42 } });
        const res = await jobs.awaitJob("job1");
        assertEq(res.ok, true, "Job concluído resolve com resultado");
        assertEq(res.v, 42, "Valor retornado correto");
    }

    async function test_timeout_backend() {
        bridge.mockVerificar = () => ({ status: "timed_out", resultado: { ok: false, erro: "Timeout", codigo: "JOB_TIMEOUT" } });
        const res = await jobs.awaitJob("job2");
        assertEq(res.ok, false, "Timeout resolve com ok=false");
        assertEq(res.codigo, "JOB_TIMEOUT", "Codigo de timeout correto");
    }

    async function test_cancelled() {
        bridge.mockVerificar = () => ({ status: "cancelled", resultado: { ok: false, codigo: "JOB_CANCELLED" } });
        const res = await jobs.awaitJob("job3");
        assertEq(res.ok, false, "Cancelado resolve com ok=false");
        assertEq(res.codigo, "JOB_CANCELLED", "Codigo de cancelamento correto");
    }

    async function test_abort_signal() {
        let resolveCheck;
        bridge.mockVerificar = () => new Promise(r => resolveCheck = r);
        
        const ac = new AbortController();
        const p = jobs.awaitJob("job4", { signal: ac.signal });
        p.catch(() => {}); // evita unhandled rejection
        
        let cancelCalled = false;
        bridge.mockCancelar = () => { cancelCalled = true; return {ok:true}; };
        
        await new Promise(r => setTimeout(r, 600)); // Espera o primeiro check disparar
        
        ac.abort();
        resolveCheck({ status: "running" }); // unblock fetch
        
        try {
            await p;
            assertEq(true, false, "Devia ter disparado exceção de cancelamento local");
        } catch (e) {
            assertEq(e.message, "Job cancelado localmente.", "Exceção correta para abort local");
            assertEq(cancelCalled, true, "cancelar_tarefa foi chamado no bridge");
        }
    }

    async function test_failed() {
        bridge.mockVerificar = () => ({ status: "failed", resultado: { ok: false, erro: "Erro grave", codigo: "JOB_INTERNAL_ERROR" } });
        const res = await jobs.awaitJob("job5");
        assertEq(res.ok, false, "Falha resolve com ok=false");
        assertEq(res.codigo, "JOB_INTERNAL_ERROR", "Codigo de falha interna correto");
    }

    async function runAll() {
        await test_success();
        await test_timeout_backend();
        await test_cancelled();
        await test_abort_signal();
        await test_failed();

        console.log(`\\nResultados: ${passed} OK, ${failed} Falhas.`);
        if (failed > 0) {
            process.exit(1);
        }
    }

    runAll();
}

runTest();
