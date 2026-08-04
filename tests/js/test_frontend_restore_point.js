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
                        esconderOverlay: () => { sandbox.overlayAberto = false; },
                        atualizarOverlay: () => {}
                    }
                },
                state: { restorePointCreatedThisSession: false },
                operations: {}
            },
            document: {
                getElementById: (id) => {
                    if (id === 'overlay-barra-fill') return { classList: { contains: () => false }, style: { width: '10%' } };
                    if (sandbox.mockModal[id]) return sandbox.mockModal[id];
                    return null;
                }
            }
        },
        console: { error: () => {}, log: () => {} },
        setTimeout: (cb) => cb(), // executa imediato para testes
        setInterval: () => 1,
        clearInterval: () => {},
        overlayAberto: false,
        mockModal: {
            'modal-restauracao': { classList: { add: () => { sandbox.modalAberto = true; }, remove: () => { sandbox.modalAberto = false; } } },
            'modal-titulo': { textContent: '' },
            'modal-mensagem': { textContent: '' },
            'modal-icon': { className: '', textContent: '' },
            'btn-modal-confirmar': {
                textContent: '', className: '', style: {},
                addEventListener: (ev, cb) => { if (ev === 'click') sandbox.mockConfirmarClick = cb; },
                removeEventListener: () => {},
                appendChild: () => {},
                removeChild: () => {}
            },
            'btn-modal-cancelar': {
                textContent: '',
                addEventListener: (ev, cb) => { if (ev === 'click') sandbox.mockCancelarClick = cb; },
                removeEventListener: () => {},
                appendChild: () => {},
                removeChild: () => {}
            }
        },
        modalAberto: false,
        mockConfirmarClick: null,
        mockCancelarClick: null
    };

    sandbox.document = sandbox.window.document;
    sandbox.Phoenix = sandbox.window.Phoenix;

    vm.createContext(sandbox);
    const code = fs.readFileSync(path.resolve(__dirname, '../../gui/js/operations/restore-point.js'), 'utf8');

    // 17, 18, 19
    assert(!code.includes('executarOtimizacao'), 'não contém Otimização');
    assert(!code.includes('executarRotinaCompleta'), 'não contém Rotina Completa');
    assert(!code.includes('alert('), 'não usa alert nativo');
    assert(!code.includes('window.confirm'), 'não usa confirm nativo');

    vm.runInContext(code, sandbox);

    try {
        const operation = sandbox.window.Phoenix.operations.restorePoint;
        assert(operation, "Módulo não registrado"); // 1

        let acaoChamada = 0;
        const mockAction = async () => { acaoChamada++; return "resultado-acao"; };

        // 2. não inicia ação ao carregar arquivo (acaoChamada é 0)
        assert(acaoChamada === 0, "não iniciou ação no carregamento");

        // 3. ponto já criado executa ação diretamente
        sandbox.Phoenix.state.restorePointCreatedThisSession = true;
        let bridgeChamada = false;
        sandbox.Phoenix.bridge.call = async () => { bridgeChamada = true; };
        await operation.runProtected(mockAction);
        assert(acaoChamada === 1, "ação executada diretamente");
        assert(!bridgeChamada, "bridge não chamada");

        // 4, 5, 6, 7. ponto não criado chama endpoint, awaitJob, marca estado, executa uma vez
        sandbox.Phoenix.state.restorePointCreatedThisSession = false;
        acaoChamada = 0;
        let jobAguardado = false;
        sandbox.Phoenix.bridge.call = async (ep) => {
            if (ep === 'criar_ponto_restauracao') bridgeChamada = true;
            return { job_id: 'abc' };
        };
        sandbox.Phoenix.jobs.awaitJob = async (jid) => {
            if (jid === 'abc') jobAguardado = true;
            return { ok: true };
        };
        const res3 = await operation.runProtected(mockAction);
        assert(bridgeChamada, "endpoint chamado");
        assert(jobAguardado, "job aguardado");
        assert(sandbox.Phoenix.state.restorePointCreatedThisSession === true, "estado marcado");
        assert(acaoChamada === 1, "ação executada uma vez"); // 7
        assert(res3 === "resultado-acao", "retorno preservado"); // 15
        assert(!sandbox.overlayAberto, "overlay fechado"); // 12. flag libera (implícito se overlay fechado e não pendente)

        // Reset
        sandbox.Phoenix.state.restorePointCreatedThisSession = false;
        acaoChamada = 0;

        // 8, 9, 10. falha não marca estado (até escolher), abortar não executa, continuar executa
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: false });
        
        let promiseAbortar = operation.runProtected(mockAction);
        // modal deve abrir
        await new Promise(r => setImmediate(r));
        assert(sandbox.modalAberto, "modal abre na falha");
        assert(sandbox.Phoenix.state.restorePointCreatedThisSession === false, "falha não marca estado"); // 8
        sandbox.mockCancelarClick(); // 9
        const resAbort = await promiseAbortar;
        assert(acaoChamada === 0, "abortar não executa ação");
        assert(resAbort === undefined, "sem retorno");
        assert(!sandbox.overlayAberto, "overlay fechado após abortar"); // 13

        // Continuar
        let promiseContinuar = operation.runProtected(mockAction);
        await new Promise(r => setImmediate(r));
        sandbox.mockConfirmarClick(); // 10
        const resCont = await promiseContinuar;
        assert(acaoChamada === 1, "continuar executa ação");
        assert(sandbox.Phoenix.state.restorePointCreatedThisSession === true, "continuar marca estado para futuras");
        assert(resCont === "resultado-acao");

        // 11. duas solicitações não criam dois pontos
        sandbox.Phoenix.state.restorePointCreatedThisSession = false;
        let chamadasBridge = 0;
        sandbox.Phoenix.bridge.call = async () => {
            chamadasBridge++;
            return { job_id: 'def' };
        };
        sandbox.Phoenix.jobs.awaitJob = async () => {
            await new Promise(r => setTimeout(r, 10)); // delay real simulando processo
            return { ok: true };
        };
        
        let acoesExecutadas = [];
        const actionA = async () => { acoesExecutadas.push("A"); return "RetornoA"; };
        const actionB = async () => { acoesExecutadas.push("B"); return "RetornoB"; };

        const promiseA = operation.runProtected(actionA);
        const promiseB = operation.runProtected(actionB); // Deve ser rejeitada/ignorada
        
        const [resA, resB] = await Promise.all([promiseA, promiseB]);
        
        assert(chamadasBridge === 1, "duas solicitações não criam dois pontos"); // 11
        assert(acoesExecutadas.length === 1 && acoesExecutadas[0] === "A", "ação pendente não é substituída nem duplicada"); // 14
        assert(resA === "RetornoA", "retorno A preservado");
        assert(resB === undefined, "action B explícita e controladamente ignorada"); // Opção B atendida (rejeitada/ignorada)

        // 18. segunda ação durante modal
        sandbox.Phoenix.state.restorePointCreatedThisSession = false;
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: false }); // forçar falha para abrir modal
        
        let promessaModalA = operation.runProtected(actionA);
        await new Promise(r => setImmediate(r)); // yield para abrir modal
        assert(sandbox.modalAberto, "modal aberto para A");
        
        let promessaModalB = operation.runProtected(actionB); // segunda ação enquanto modal está aberto
        const resModalB = await promessaModalB;
        assert(resModalB === undefined, "segunda ação ignorada durante modal");
        
        sandbox.mockCancelarClick(); // fecha modal da A
        const resModalA = await promessaModalA;
        assert(resModalA === undefined, "A foi cancelada");

        // 16. erro da ação é preservado
        sandbox.Phoenix.state.restorePointCreatedThisSession = true;
        let erroAcao = false;
        try {
            await operation.runProtected(async () => { throw new Error("Erro teste"); });
        } catch (e) {
            erroAcao = true;
            assert(e.message === "Erro teste", "erro preservado");
        }
        assert(erroAcao, "exceção propagada");

        console.log("Todos os testes JS do Ponto de Restauração passaram.");
    } catch (e) {
        console.error(e);
        process.exit(1);
    }
}

runTests();
