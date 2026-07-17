const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

async function runTests() {
    const sandbox = {
        window: {
            Phoenix: {
                bridge: { call: async () => ({ job_id: '123' }) },
                jobs: { awaitJob: async () => ({ ok: true }) },
                ui: {
                    feedback: {
                        mostrarOverlay: () => { sandbox.overlayAberto = true; },
                        esconderOverlay: () => { sandbox.overlayAberto = false; }
                    }
                },
                state: {},
                operations: {
                    restorePoint: {
                        runProtected: async (fn) => await fn()
                    }
                },
                pages: {}
            },
            document: {
                getElementById: (id) => {
                    return sandbox.mockDom[id] || null;
                }
            }
        },
        console: { error: () => {}, log: () => {} },
        overlayAberto: false,
        mockDom: {
            'btn-otimizacao-geral': { dataset: {}, addEventListener: (ev, cb) => { if (ev === 'click') sandbox.clicks.geral = cb; } },
            'btn-otimizacao-gaming': { dataset: {}, addEventListener: (ev, cb) => { if (ev === 'click') sandbox.clicks.gaming = cb; } },
            'btn-otimizar-disco': { dataset: {}, addEventListener: (ev, cb) => { if (ev === 'click') sandbox.clicks.disco = cb; } },
            'btn-liberar-ram': { dataset: {}, addEventListener: (ev, cb) => { if (ev === 'click') sandbox.clicks.ram = cb; } },
            'btn-analisar-startup': { dataset: {}, addEventListener: (ev, cb) => { if (ev === 'click') sandbox.clicks.startup = cb; } },
            'resultado-otimizacao': { innerHTML: '' },
            'resultado-startup': { innerHTML: '', style: {} }
        },
        clicks: {}
    };

    sandbox.document = sandbox.window.document;
    sandbox.Phoenix = sandbox.window.Phoenix;

    vm.createContext(sandbox);
    const code = fs.readFileSync(path.resolve(__dirname, '../../gui/js/pages/otimizacao.js'), 'utf8');

    // 45, 46, 47, 48
    assert(!code.includes('carregarServicos'), 'não contém Serviços');
    assert(!code.includes('carregarHistorico'), 'não contém Histórico');
    assert(!code.includes('renderizarRelatorio'), 'não contém Relatório');
    assert(!code.includes('executarRotinaCompleta'), 'não contém Rotina Completa');

    vm.runInContext(code, sandbox);

    try {
        const page = sandbox.window.Phoenix.pages.otimizacao;
        assert(page, "Módulo não registrado"); // 1

        page.load(); // 2
        assert(sandbox.clicks.geral, "listener geral registrado"); // 3

        let listenersDuplicados = false;
        sandbox.mockDom['btn-otimizacao-geral'].addEventListener = () => { listenersDuplicados = true; };
        page.load();
        assert(!listenersDuplicados, "não duplica listeners"); // 4

        // 5-10 Geral
        let endpoint = null;
        sandbox.Phoenix.bridge.call = async (ep) => { endpoint = ep; return { job_id: '123' }; };
        let jobAguardado = false;
        sandbox.Phoenix.jobs.awaitJob = async (jid) => { if (jid === '123') jobAguardado = true; return { ok: true }; };
        let protegido = false;
        sandbox.Phoenix.operations.restorePoint.runProtected = async (fn) => { protegido = true; await fn(); };
        
        const p1 = page.executeGeneral();
        const p2 = page.executeGeneral(); // duplo clique
        await Promise.all([p1, p2]);
        assert(endpoint === 'executar_otimizacao_geral', "endpoint correto"); // 5
        assert(protegido, "usa ponto de restauração"); // 6
        assert(jobAguardado, "job aguardado"); // 7
        assert(sandbox.mockDom['resultado-otimizacao'].innerHTML.includes('Concluído'), "sucesso"); // 8
        assert(!sandbox.overlayAberto, "overlay fecha");

        // erro geral
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: false, erro: 'falha x' });
        await page.executeGeneral();
        assert(sandbox.mockDom['resultado-otimizacao'].innerHTML.includes('Erro'), "erro"); // 9
        assert(!sandbox.overlayAberto, "overlay fecha no erro");
        // duplo clique bloqueado (p2 não lançou erro nem mudou estado) // 10

        // 11-16 Gaming
        endpoint = null; protegido = false; jobAguardado = false;
        sandbox.Phoenix.bridge.call = async (ep, arg) => { endpoint = ep; assert(arg === false); return { job_id: '123' }; };
        sandbox.Phoenix.jobs.awaitJob = async () => { jobAguardado = true; return { ok: true }; };
        await page.executeGaming();
        assert(endpoint === 'executar_otimizacao_gaming', "endpoint correto"); // 11
        assert(protegido, "proteção correta"); // 12
        assert(jobAguardado, "job aguardado"); // 13
        assert(sandbox.mockDom['resultado-otimizacao'].innerHTML.includes('Concluído'), "sucesso"); // 14

        // 17-22 Disco
        endpoint = null; protegido = false;
        sandbox.Phoenix.bridge.call = async (ep) => { endpoint = ep; return { job_id: '123' }; };
        await page.optimizeDisk();
        assert(endpoint === 'otimizar_disco', "endpoint correto"); // 17
        assert(!protegido, "política real (não usa restore point)"); // 18
        assert(sandbox.mockDom['resultado-otimizacao'].innerHTML.includes('Concluído'), "sucesso"); // 20

        // 23-27 Memória
        endpoint = null; protegido = false;
        sandbox.Phoenix.bridge.call = async (ep) => { endpoint = ep; return { job_id: '123' }; };
        sandbox.overlayAberto = true; // reset
        await page.releaseStandbyMemory();
        assert(endpoint === 'liberar_memoria_standby', "endpoint correto"); // 23
        assert(!protegido, "política real"); // 24
        assert(!sandbox.overlayAberto, "overlay fecha");

        // 28-33 Startup
        endpoint = null;
        sandbox.Phoenix.bridge.call = async (ep) => { endpoint = ep; return { job_id: '123' }; };
        sandbox.Phoenix.jobs.awaitJob = async () => { return { ok: true, entradas: [{nome:'a',raiz:'HKLM'}] }; };
        await page.analyzeStartup();
        assert(endpoint === 'analisar_startup'); // 29, 30
        assert(sandbox.mockDom['resultado-startup'].innerHTML.includes('encontrados no startup'), "renderização"); // 31
        
        console.log("Todos os testes JS da Página Otimização passaram.");
    } catch (e) {
        console.error(e);
        process.exit(1);
    }
}

runTests();
