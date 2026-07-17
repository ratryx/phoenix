const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

async function runTests() {
    const sandbox = {
        window: {
            Phoenix: {
                bridge: { call: async () => ({ job_id: '123' }) },
                jobs: { awaitJob: async () => ({ ok: true, espaco_liberado_mb: 150 }) },
                ui: {
                    feedback: {
                        mostrarOverlay: () => { sandbox.overlayAberto = true; },
                        esconderOverlay: () => { sandbox.overlayAberto = false; },
                        confirmarModal: async () => true
                    }
                },
                state: {},
                pages: {}
            },
            document: {
                getElementById: (id) => {
                    if (id === 'btn-executar-limpeza') return sandbox.mockBtn;
                    if (id === 'conteudo-limpeza') return sandbox.mockContainer;
                    return null;
                }
            }
        },
        console: { error: () => {}, log: () => {} },
        setTimeout: setTimeout,
        clearTimeout: clearTimeout,
        overlayAberto: false,
        mockBtn: {
            dataset: {},
            addEventListener: (ev, cb) => {
                if (ev === 'click') sandbox.mockBtn.onclick = cb;
            }
        },
        mockContainer: { innerHTML: '' }
    };

    sandbox.document = sandbox.window.document;
    sandbox.Phoenix = sandbox.window.Phoenix;

    vm.createContext(sandbox);

    const code = fs.readFileSync(path.resolve(__dirname, '../../gui/js/pages/limpeza.js'), 'utf8');
    vm.runInContext(code, sandbox);

    try {
        const page = sandbox.window.Phoenix.pages.limpeza;
        assert(page, "Módulo não registrado como Phoenix.pages.limpeza");

        // 1. Carregamento e listener
        page.load();
        assert(sandbox.mockBtn.onclick, "Listener registrado no botão");
        assert(sandbox.mockBtn.dataset.eventosRegistrados === "true", "Guard de listener atualizado");

        // 2. Confirmação = Cancelar
        let calledBridge = false;
        sandbox.Phoenix.bridge.call = async () => { calledBridge = true; return { job_id: '123' }; };
        sandbox.Phoenix.ui.feedback.confirmarModal = async (titulo, texto) => {
            assert(titulo === "Confirmação", "modal recebe textos corretos");
            return false;
        };
        
        await sandbox.mockBtn.onclick();
        assert(!calledBridge, "cancelar não chama bridge");
        assert(!sandbox.overlayAberto, "cancelamento não abre overlay destrutivo");

        // 3. Execução = Sucesso
        sandbox.Phoenix.ui.feedback.confirmarModal = async () => true;
        sandbox.Phoenix.ui.feedback.mostrarOverlay = () => { sandbox.overlayAberto = true; };
        sandbox.Phoenix.ui.feedback.esconderOverlay = () => { sandbox.overlayAberto = false; };
        calledBridge = false;
        let jobCalled = false;
        sandbox.Phoenix.bridge.call = async (ep) => {
            assert(ep === "executar_limpeza", "endpoint correto");
            calledBridge = true;
            return { job_id: '456' };
        };
        sandbox.Phoenix.jobs.awaitJob = async (jid) => {
            assert(jid === '456', "retorno job_id aguardado");
            jobCalled = true;
            await new Promise(r => setTimeout(r, 20)); // Delay to test overlay state
            return { ok: true, espaco_liberado_mb: 500 };
        };

        let execPromise = sandbox.mockBtn.onclick();
        // Wait for event loop to process microtasks
        await new Promise(r => setTimeout(r, 10));
        assert(sandbox.overlayAberto, "overlay abre");
        
        // 4. Proteção contra duplicação (Concorrência)
        let callCount = 0;
        sandbox.Phoenix.bridge.call = async () => { callCount++; return { job_id: '1' }; };
        let execPromise2 = sandbox.mockBtn.onclick(); // deveria retornar imediatamente por estar executando
        await Promise.all([execPromise, execPromise2]);
        
        assert(jobCalled, "job concluído processado");
        assert(!sandbox.overlayAberto, "overlay não permanece aberto");
        assert(sandbox.mockContainer.innerHTML.includes("Concluído"), "markup principal preservado");
        assert(sandbox.mockContainer.innerHTML.includes("500.0 MB"), "total liberado renderizado");

        // Flag liberada em sucesso
        callCount = 0;
        await sandbox.mockBtn.onclick(); // Roda de novo
        assert(callCount === 1, "flag liberada em sucesso");

        // 5. Tratamento de falhas: `{ok: false}`
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: false, erro: "Algo falhou" });
        await sandbox.mockBtn.onclick();
        assert(sandbox.mockContainer.innerHTML.includes("Algo falhou"), "{ok: false} tratado");
        assert(sandbox.mockContainer.innerHTML.includes("Erro"), "zero MB tratado indiretamente em falha");
        
        // 6. Tratamento de falhas: Bridge Error
        sandbox.Phoenix.bridge.call = async () => { throw new Error("bridge error"); };
        await sandbox.mockBtn.onclick();
        assert(!sandbox.overlayAberto, "overlay não permanece aberto após erro");
        
        // Flag liberada em erro
        sandbox.Phoenix.bridge.call = async () => ({ job_id: '1' });
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: true, espaco_liberado_mb: 0 });
        await sandbox.mockBtn.onclick();
        assert(sandbox.mockContainer.innerHTML.includes("0.0 MB"), "zero MB tratado");

        // 7. Limites
        assert(!code.includes("executarOtimizacao"), "módulo não contém otimização");
        assert(!code.includes("carregarServicos"), "módulo não contém serviços");
        assert(!code.includes("executarRotinaCompleta"), "módulo não contém rotina completa");

        console.log("Todos os testes JS de limpeza passaram.");

    } catch (e) {
        console.error(e);
        process.exit(1);
    }
}

runTests();
