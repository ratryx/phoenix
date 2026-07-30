const fs = require('fs');
const vm = require('vm');

function runTest() {
    console.log("=== INICIANDO TESTES DO JOBS ===");
    const code = fs.readFileSync('gui/js/core/jobs.js', 'utf8');

    let bridgeCalls = [];
    const bridge = {
        call: async (method, ...args) => {
            bridgeCalls.push({ method, args });
            if (method === "verificar_tarefa") return bridge.mockVerificar(args[0]);
            if (method === "cancelar_tarefa") return bridge.mockCancelar(args[0]);
        },
        mockVerificar: (id) => ({ status: "running" }),
        mockCancelar: (id) => ({ ok: true })
    };

    const timers = [];
    let timerCounter = 1;
    function fakeSetTimeout(cb, delay) {
        const id = timerCounter++;
        timers.push({ id, cb, delay, active: true });
        return id;
    }
    function fakeClearTimeout(id) {
        const t = timers.find(t => t.id === id);
        if (t) t.active = false;
    }

    async function stepTimer() {
        let t = null;
        while (timers.length > 0) {
            let next = timers.shift();
            if (next.active) {
                t = next;
                break;
            }
        }
        if (t) {
            const res = t.cb();
            if (res && typeof res.then === 'function') await res;
            else await Promise.resolve(); // yield to microtask queue
        }
    }

    const Phoenix = { bridge, jobs: {} };
    const context = {
        window: { Phoenix }, Phoenix, console,
        setTimeout: fakeSetTimeout, clearTimeout: fakeClearTimeout,
        AbortController, Promise
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

    async function runCase(name, fn) {
        try {
            timers.length = 0;
            bridgeCalls = [];
            bridge.mockVerificar = (id) => ({ status: "running" });
            bridge.mockCancelar = (id) => ({ ok: true });
            await fn();
        } catch (err) {
            console.error(`❌ [FALHA] ${name}: exceção não tratada - ${err}`);
            failed++;
        }
    }

    async function runAll() {
        // 1. awaitJob(jobId)
        await runCase("1. awaitJob(jobId)", async () => {
            bridge.mockVerificar = () => ({ status: "done", resultado: { ok: true, v: 1 } });
            let p = jobs.awaitJob("j1");
            await stepTimer();
            let res = await p;
            assertEq(res.v, 1, "resolveu job");
        });

        // 2. awaitJob(jobId, progressCallback)
        await runCase("2. awaitJob(jobId, progressCallback)", async () => {
            let progress = 0;
            bridge.mockVerificar = () => {
                if (progress === 0) { progress = 10; return { status: "running", progresso: 10 }; }
                return { status: "done", resultado: { ok: true } };
            };
            let p = jobs.awaitJob("j2", (pct) => { progress = pct; });
            await stepTimer(); // gets 10
            await stepTimer(); // gets done
            await p;
            assertEq(progress, 10, "callback invocado");
        });

        // 3. awaitJob(jobId, options)
        await runCase("3. awaitJob(jobId, options)", async () => {
            bridge.mockVerificar = () => ({ status: "done", resultado: { ok: true } });
            let p = jobs.awaitJob("j3", { pollIntervalMs: 200 });
            assertEq(timers[0].delay, 200, "usou poll interval 200");
            await stepTimer();
            await p;
        });

        // 4. awaitJob(jobId, progressCallback, options)
        await runCase("4. awaitJob(jobId, progressCallback, options)", async () => {
            let progress = 0;
            bridge.mockVerificar = () => {
                if (progress === 0) { progress = 20; return { status: "running", progresso: 20 }; }
                return { status: "done", resultado: { ok: true } };
            };
            let p = jobs.awaitJob("j4", (pct) => { progress = pct; }, { pollIntervalMs: 300 });
            assertEq(timers[0].delay, 300, "usou poll interval 300");
            await stepTimer();
            await stepTimer();
            await p;
            assertEq(progress, 20, "callback invocado overload triplo");
        });

        // 5. custom valid pollIntervalMs
        await runCase("5. custom valid pollIntervalMs", async () => {
            jobs.awaitJob("j5", { pollIntervalMs: 150 });
            assertEq(timers[0].delay, 150, "usou 150ms");
        });

        // 6. invalid/small pollIntervalMs fallback
        await runCase("6. invalid/small pollIntervalMs fallback", async () => {
            jobs.awaitJob("j6_1", { pollIntervalMs: 50 });
            assertEq(timers[0].delay, 500, "50ms virou 500ms");
            timers.length = 0;
            jobs.awaitJob("j6_2", { pollIntervalMs: "asd" });
            assertEq(timers[0].delay, 500, "NaN virou 500ms");
        });

        // 7. running then done
        await runCase("7. running then done", async () => {
            let calls = 0;
            bridge.mockVerificar = () => {
                calls++;
                if (calls === 1) return { status: "running" };
                return { status: "done", resultado: { ok: true, step: "final" } };
            };
            let p = jobs.awaitJob("j7");
            await stepTimer();
            await stepTimer();
            let res = await p;
            assertEq(res.step, "final", "terminou sucesso");
        });

        // 8. backend failed
        await runCase("8. backend failed", async () => {
            bridge.mockVerificar = () => ({ status: "failed", resultado: { ok: false, codigo: "ERR1" } });
            let p = jobs.awaitJob("j8");
            await stepTimer();
            let res = await p;
            assertEq(res.codigo, "ERR1", "retornou erro interno");
        });

        // 9. backend cancelled
        await runCase("9. backend cancelled", async () => {
            bridge.mockVerificar = () => ({ status: "cancelled", resultado: { ok: false, codigo: "CANC1" } });
            let p = jobs.awaitJob("j9");
            await stepTimer();
            let res = await p;
            assertEq(res.codigo, "CANC1", "retornou cancelado");
        });

        // 10. backend timed_out
        await runCase("10. backend timed_out", async () => {
            bridge.mockVerificar = () => ({ status: "timed_out", resultado: { ok: false, codigo: "TOUT1" } });
            let p = jobs.awaitJob("j10");
            await stepTimer();
            let res = await p;
            assertEq(res.codigo, "TOUT1", "retornou timed_out");
        });

        // 11. not_found
        await runCase("11. not_found", async () => {
            bridge.mockVerificar = () => ({ status: "not_found" });
            let p = jobs.awaitJob("j11");
            await stepTimer();
            try {
                await p;
                assertEq(true, false, "deveria dar throw em not_found");
            } catch (err) {
                assertEq(err.message, "Falha na consulta de status do processo interno.", "throw de not_found correto");
            }
        });

        // 12. status bridge rejection
        await runCase("12. status bridge rejection", async () => {
            bridge.mockVerificar = () => Promise.reject(new Error("bridge fail"));
            let p = jobs.awaitJob("j12");
            await stepTimer();
            try {
                await p;
                assertEq(true, false, "deveria dar throw");
            } catch (err) {
                assertEq(err.message, "bridge fail", "rejeita com o erro do bridge");
            }
        });

        // 13. signal already aborted
        await runCase("13. signal already aborted", async () => {
            const ac = new AbortController();
            ac.abort();
            let p = jobs.awaitJob("j13", { signal: ac.signal });
            let res = await p;
            assertEq(res.codigo, "JOB_CANCELLED", "abortado early");
            assertEq(timers.filter(t => t.active).length, 0, "não criou timer");
        });

        // 14. abort during an in-flight status query
        await runCase("14. abort during an in-flight status query", async () => {
            const ac = new AbortController();
            let resolveVerificar;
            bridge.mockVerificar = () => new Promise(res => { resolveVerificar = res; });

            let p = jobs.awaitJob("j14", { signal: ac.signal });
            await stepTimer(); // fires first check, blocked on resolveVerificar
            ac.abort(); // abort in flight

            let res = await p;
            assertEq(res.codigo, "JOB_CANCELLED", "abortado in flight");

            resolveVerificar({ status: "done", resultado: { ok: true } });
            await Promise.resolve(); // wait tick

            // Should not schedule any more timers
            assertEq(timers.filter(t => t.active).length, 0, "nenhum timer novo");
        });

        // 15. cancellation bridge rejection produces no unhandled rejection
        await runCase("15. cancellation bridge rejection produces no unhandled rejection", async () => {
            const ac = new AbortController();
            bridge.mockCancelar = () => Promise.reject(new Error("cancellation bridge errored"));
            let p = jobs.awaitJob("j15", { signal: ac.signal });
            ac.abort();
            let res = await p;
            assertEq(res.codigo, "JOB_CANCELLED", "sucesso no abort");
            // Node would crash with unhandled rejection if it wasn't swallowed
            await Promise.resolve();
        });

        // 16. cancelar_tarefa is invoked exactly once
        await runCase("16. cancelar_tarefa is invoked exactly once", async () => {
            const ac = new AbortController();
            let cancelCalls = 0;
            bridge.mockCancelar = () => { cancelCalls++; return { ok: true }; };
            let p = jobs.awaitJob("j16", { signal: ac.signal });
            ac.abort();
            ac.abort(); // call it twice
            let res = await p;
            assertEq(cancelCalls, 1, "cancelar_tarefa chamado apenas uma vez");
        });

        // 17. no timer or polling after settlement
        await runCase("17. no timer or polling after settlement", async () => {
            bridge.mockVerificar = () => ({ status: "done", resultado: { ok: true } });
            let p = jobs.awaitJob("j17");
            await stepTimer();
            await p;
            assertEq(timers.filter(t => t.active).length, 0, "nenhum timer apos settled");
        });

        // 18. no progress callback after abort/settlement
        await runCase("18. no progress callback after abort/settlement", async () => {
            const ac = new AbortController();
            let prog = 0;
            let resolveVerificar;
            bridge.mockVerificar = () => new Promise(res => { resolveVerificar = res; });

            let p = jobs.awaitJob("j18", (pct) => { prog++; }, { signal: ac.signal });
            await stepTimer(); // in flight
            ac.abort();
            await p;
            resolveVerificar({ status: "running", progresso: 50 });
            await Promise.resolve();
            assertEq(prog, 0, "prog nao pode ser chamado");
        });

        // 19. two concurrent jobs remain independent
        await runCase("19. two concurrent jobs remain independent", async () => {
            let reqs = [];
            bridge.mockVerificar = (id) => {
                reqs.push(id);
                if (id === "j19_a") return { status: "done", resultado: { ok: true, r: "a" } };
                if (id === "j19_b") return { status: "running", progresso: 10 };
            };
            let pA = jobs.awaitJob("j19_a");
            let pB = jobs.awaitJob("j19_b");

            await stepTimer(); // j19_a done
            let resA = await pA;
            assertEq(resA.r, "a", "A terminou");

            await stepTimer(); // j19_b running
            assertEq(reqs.includes("j19_b"), true, "B fez requisicao");
        });

        console.log(`\nResultados: ${passed} OK, ${failed} Falhas.`);
        if (failed > 0) process.exit(1);
    }

    runAll().then(() => {
        // all good
    }).catch(err => {
        console.error(err);
        process.exit(1);
    });
}

runTest();
