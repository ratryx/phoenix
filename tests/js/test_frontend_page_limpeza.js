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
                },
                createElement: (tag) => {
                    return {
                        textContent: '',
                        innerHTML: '',
                        style: {},
                        appendChild: function(c) { this.innerHTML += c.textContent || c.innerHTML || ''; }
                    };
                },
                createTextNode: (txt) => {
                    return { textContent: txt };
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
        mockContainer: {
            innerHTML: '',
            appendChild: function(child) { this.innerHTML += child.textContent || child.innerHTML || ''; },
            replaceChildren: function() { this.innerHTML = ''; }
        },
        AbortController: class {
            constructor() { this.signal = { aborted: false }; }
            abort() {}
        }
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

        // 2. Execução = Sucesso
        sandbox.Phoenix.ui.feedback.mostrarOverlay = () => { sandbox.overlayAberto = true; };
        sandbox.Phoenix.ui.feedback.esconderOverlay = () => { sandbox.overlayAberto = false; };

        let calledBridge = false;
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

        // 3. Proteção contra duplicação (Concorrência)
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
        sandbox.Phoenix.bridge.call = async () => { callCount++; return { job_id: '1' }; };
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: true, espaco_liberado_mb: 100 });
        await sandbox.mockBtn.onclick(); // Roda de novo
        assert(callCount === 1, "flag liberada em sucesso");

        // 4b. Tratamento de parcial: {ok: true, parcial: true}
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: true, parcial: true, espaco_liberado_mb: 15 });
        await sandbox.mockBtn.onclick();
        assert(sandbox.mockContainer.innerHTML.includes("15.0 MB"), "15 MB renderizado no parcial");
        assert(sandbox.mockContainer.innerHTML.includes("Concluído (Parcial)"), "parcial tratado");

        // 4. Tratamento de falhas: `{ok: false}`
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: false, erro: "Algo falhou" });
        await sandbox.mockBtn.onclick();
        assert(sandbox.mockContainer.innerHTML.includes("Algo falhou"), "{ok: false} tratado");
        assert(sandbox.mockContainer.innerHTML.includes("Erro"), "erro é renderizado");

        // 4c. Tratamento de cancelamento na UI (AbortController e signal)
        let cancelBtnDisabled = false;
        let cancelBtnText = "";
        let abortCalled = false;

        sandbox.AbortController = class {
            constructor() { this.signal = { aborted: false }; }
            abort() { abortCalled = true; }
        };

        const mockCancelBtn = {
            disabled: false,
            textContent: "Cancelar",
            onclick: null
        };
        sandbox.document.getElementById = (id) => {
            if (id === 'btn-executar-limpeza') return sandbox.mockBtn;
            if (id === 'conteudo-limpeza') return sandbox.mockContainer;
            if (id === 'overlay-btn-cancelar') return mockCancelBtn;
            return null;
        };

        sandbox.Phoenix.jobs.awaitJob = async (jid, opts) => {
            assert(opts.signal !== undefined, "Signal deve ser passado para awaitJob");
            // simular clique do usuário no botão cancelar
            mockCancelBtn.onclick();
            assert(mockCancelBtn.disabled === true, "Botão cancelar deve ficar desabilitado");
            assert(mockCancelBtn.textContent === "Cancelando...", "Botão cancelar texto deve mudar");
            assert(abortCalled === true, "Controller deve ter sido abortado");

            return {
                ok: false,
                codigo: "JOB_CANCELLED",
                erro: "A operação foi cancelada.",
                resultado_parcial: { espaco_liberado_bytes: 10485760, arquivos_processados: 10, arquivos_removidos: 8, arquivos_ignorados: 2, categoria: "Cache do Chrome" }
            };
        };
        await sandbox.mockBtn.onclick();
        assert(sandbox.mockContainer.innerHTML.includes("Cancelado"), "JOB_CANCELLED gera tag Cancelado");
        assert(sandbox.mockContainer.innerHTML.includes("10 itens processados"), "Renderiza itens processados no cancelamento");
        assert(sandbox.mockContainer.innerHTML.includes("10.0 MB"), "Renderiza MB convertidos no cancelamento");
        assert(sandbox.mockContainer.innerHTML.includes("Cache do Chrome"), "Renderiza categoria onde parou");
        assert(mockCancelBtn.onclick === null, "Listener de cancelar deve ser limpo");

        // 4d. Tratamento de TIMEOUT com snapshot
        sandbox.Phoenix.jobs.awaitJob = async () => ({
            ok: false,
            codigo: "JOB_TIMEOUT",
            erro: "Timeout.",
            resultado_parcial: { espaco_liberado_mb: 25.5, arquivos_processados: 5 }
        });
        await sandbox.mockBtn.onclick();
        assert(sandbox.mockContainer.innerHTML.includes("Erro"), "JOB_TIMEOUT continua como Erro");
        assert(sandbox.mockContainer.innerHTML.includes("25.5 MB liberados antes da interrupção"), "Renderiza mb direto do parcial no timeout");

        // 5. Tratamento de falhas: Bridge Error
        sandbox.Phoenix.bridge.call = async () => { throw new Error("bridge error"); };
        await sandbox.mockBtn.onclick();
        assert(!sandbox.overlayAberto, "overlay não permanece aberto após erro");

        // Flag liberada em erro
        sandbox.Phoenix.bridge.call = async () => ({ job_id: '1' });
        sandbox.Phoenix.jobs.awaitJob = async () => ({ ok: true, espaco_liberado_mb: 0 });
        await sandbox.mockBtn.onclick();
        assert(sandbox.mockContainer.innerHTML.includes("0.0 MB"), "zero MB tratado");

        // 6. Limites
        assert(!code.includes("executarOtimizacao"), "módulo não contém otimização");
        assert(!code.includes("carregarServicos"), "módulo não contém serviços");
        assert(!code.includes("executarRotinaCompleta"), "módulo não contém rotina completa");
        assert(!code.includes("confirmarModal"), "não existe chamada a confirmarModal");
        assert(!code.includes("window.confirm"), "não existe chamada a window.confirm");
        assert(!code.includes("alert("), "não existe chamada a alert");

        console.log("Todos os testes JS de limpeza passaram.");

    } catch (e) {
        console.error(e);
        process.exit(1);
    }
}

runTests();
