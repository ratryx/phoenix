const fs = require('fs');
const vm = require('vm');

function runTest() {
    console.log("=== INICIANDO TESTES DO JOBS ===");
    const code = fs.readFileSync('gui/js/core/jobs.js', 'utf8');

    const bridge = {
        call: async (method, ...args) => {
            if (method === "verificar_tarefa") return bridge.mockVerificar(args[0]);
            if (method === "cancelar_tarefa") return bridge.mockCancelar(args[0]);
        },
        mockVerificar: (id) => ({ status: "running" }),
        mockCancelar: (id) => ({ ok: true })
    };

    const Phoenix = { bridge, jobs: {} };
    const context = { 
        window: { Phoenix }, Phoenix, console, 
        setTimeout, clearTimeout, AbortController, Promise 
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
            passed++;
        }
    }

    async function test_overload_cb_only() {
        let cb_called = false;
        let checks = 0;
        bridge.mockVerificar = () => {
            checks++;
            if (checks === 1) return { status: "running", progresso: 50 };
            return { status: "done", resultado: {ok:true} };
        };
        await jobs.awaitJob("j_cb_only", (pct) => { if(pct===50) cb_called = true; });
        assertEq(cb_called, true, "Overload (jobId, cb) - CB called");
    }

    async function test_overload_options_only() {
        let cb_called = false;
        let checks = 0;
        bridge.mockVerificar = () => {
            checks++;
            if (checks === 1) return { status: "running", progresso: 50 };
            return { status: "done", resultado: {ok:true} };
        };
        await jobs.awaitJob("j_opt_only", { 
            pollIntervalMs: 100, 
            progressCallback: (pct) => { if(pct===50) cb_called = true; }
        });
        assertEq(cb_called, true, "Overload (jobId, options) - CB called");
    }

    async function test_overload_cb_and_options() {
        let cb_called = false;
        let checks = 0;
        bridge.mockVerificar = () => {
            checks++;
            if (checks === 1) return { status: "running", progresso: 50 };
            return { status: "done", resultado: {ok:true} };
        };
        await jobs.awaitJob("j_cb_and_opt", 
            (pct) => { if(pct===50) cb_called = true; },
            { pollIntervalMs: 100 }
        );
        assertEq(cb_called, true, "Overload (jobId, cb, options) - CB called");
    }
    
    async function test_not_found_rejection() {
        bridge.mockVerificar = () => ({ status: "not_found" });
        try {
            await jobs.awaitJob("j_not_found", {pollIntervalMs:100});
            assertEq(true, false, "Devia ter falhado o job not_found");
        } catch (e) {
            assertEq(e.message, "Falha na consulta de status do processo interno.", "Erro not_found capturado corretamente");
        }
    }
    
    async function test_abort_signal_aborted_early() {
        const ac = new AbortController();
        ac.abort();
        
        bridge.mockCancelar = (id) => { return {ok:true}; };
        let res = await jobs.awaitJob("j_abort_early", { signal: ac.signal });
        assertEq(res.ok, false, "Abortado antes ok=false");
        assertEq(res.codigo, "JOB_CANCELLED", "Abortado antes cod");
    }

    async function test_success() {
        bridge.mockVerificar = () => ({ status: "done", resultado: { ok: true, v: 42 } });
        const res = await jobs.awaitJob("job1", {pollIntervalMs: 100});
        assertEq(res.ok, true, "Job concluído resolve com resultado");
        assertEq(res.v, 42, "Valor retornado correto");
    }

    async function test_timeout_backend() {
        bridge.mockVerificar = () => ({ status: "timed_out", resultado: { ok: false, erro: "Timeout", codigo: "JOB_TIMEOUT" } });
        const res = await jobs.awaitJob("job2", {pollIntervalMs: 100});
        assertEq(res.ok, false, "Timeout resolve com ok=false");
        assertEq(res.codigo, "JOB_TIMEOUT", "Codigo de timeout correto");
    }

    async function test_failed() {
        bridge.mockVerificar = () => ({ status: "failed", resultado: { ok: false, erro: "Erro grave", codigo: "JOB_INTERNAL_ERROR" } });
        const res = await jobs.awaitJob("job5", {pollIntervalMs: 100});
        assertEq(res.ok, false, "Falha resolve com ok=false");
        assertEq(res.codigo, "JOB_INTERNAL_ERROR", "Codigo de falha interna correto");
    }

    async function runAll() {
        await test_overload_cb_only();
        await test_overload_options_only();
        await test_overload_cb_and_options();
        await test_not_found_rejection();
        await test_abort_signal_aborted_early();
        await test_success();
        await test_timeout_backend();
        await test_failed();

        console.log(`\\nResultados: ${passed} OK, ${failed} Falhas.`);
        if (failed > 0) process.exit(1);
    }

    runAll();
}

runTest();
