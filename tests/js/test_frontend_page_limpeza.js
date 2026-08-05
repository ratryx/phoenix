const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const htmlCode = fs.readFileSync(path.resolve(__dirname, '../../gui/index.html'), 'utf8');
assert(htmlCode.includes('id="overlay-btn-cancelar"'), "Botão cancelar existe no index.html");
assert(htmlCode.includes('id="overlay-detalhes-limpeza"'), "Contêiner detalhes limpeza no index.html");
assert(htmlCode.includes('id="overlay-categorias"'), "Contêiner categorias no index.html");
assert(htmlCode.includes('id="overlay-progresso-numerico"'), "Contêiner numérico no index.html");

async function runTests() {
    const sandbox = {
        window: {
            addEventListener: () => {},
            removeEventListener: () => {},
            Phoenix: { bridge: {}, jobs: {}, ui: { feedback: {}, icons: { create: () => ({ appendChild: () => {} }) } }, state: {}, pages: {}, lifecycle: {} }
        },
        document: {
            elements: {},
            getElementById: function(id) {
                if (!this.elements[id]) {
                    this.elements[id] = {
                        id,
                        classList: { add: () => {}, remove: () => {}, contains: () => false },
                        style: { display: '', width: '' },
                        textContent: '',
                        innerHTML: '',
                        dataset: {},
                        appendChild: function(c) { this.innerHTML += c.textContent || c.innerHTML || ''; },
                        replaceChildren: function() { this.innerHTML = ''; },
                        addEventListener: (ev, cb) => { if (ev === 'click') this.elements[id].onclick = cb; }
                    };
                }
                return this.elements[id];
            },
            createElement: function(tag) {
                return {
                    textContent: '', innerHTML: '', style: {}, classList: { add: () => {}, remove: () => {} },
                    appendChild: function(c) { this.innerHTML += c.textContent || c.innerHTML || ''; }
                };
            },
            createTextNode: (txt) => { return { textContent: txt }; }
        },
        console: { error: (e) => console.error("SANDBOX ERR:", e), log: (m) => console.log("SANDBOX LOG:", m) },
        setTimeout: (cb, t) => setTimeout(cb, 5),
        clearTimeout: clearTimeout,
        AbortController: class {
            constructor() {
                this.signal = { aborted: false, listeners: [], addEventListener: (e, cb) => this.signal.listeners.push(cb), removeEventListener: () => {} };
            }
            abort() {
                this.signal.aborted = true;
                for (let l of this.signal.listeners) l();
            }
        },
        Promise: Promise
    };

    sandbox.document.window = sandbox.window;
    sandbox.window.document = sandbox.document;
    sandbox.Phoenix = sandbox.window.Phoenix;

    vm.createContext(sandbox);

    const loadScript = (filePath) => {
        const code = fs.readFileSync(path.resolve(__dirname, '../../', filePath), 'utf8');
        vm.runInContext(code, sandbox);
    };

    loadScript('gui/js/core/jobs.js');
    loadScript('gui/js/ui/feedback.js');
    loadScript('gui/js/pages/limpeza.js');

    try {
        const page = sandbox.window.Phoenix.pages.limpeza;
        const btn = sandbox.document.getElementById('btn-executar-limpeza');
        page.load();

        let cancel_tarefa_calls = 0;
        let verificar_tarefa_calls = 0;
        let is_cancelled = false;
        
        sandbox.window.Phoenix.bridge.call = async (ep, arg) => {
            if (ep === "executar_limpeza") return { job_id: '999' };
            if (ep === "cancelar_tarefa") {
                is_cancelled = true;
                cancel_tarefa_calls++;
                return {};
            }
            if (ep === "verificar_tarefa") {
                verificar_tarefa_calls++;
                if (is_cancelled) {
                    return { status: "cancelled", resultado: { ok: false, erro: "Cancelado pelo usuário.", codigo: "JOB_CANCELLED", resultado_parcial: { arquivos_processados: 10, arquivos_total: 20, espaco_liberado_mb: 50, arquivos_removidos: 8, arquivos_ignorados: 2 } } };
                }
                return { status: "running", progresso: 50, mensagem: "Limpando", detalhes_progresso: { arquivos_processados: 10, arquivos_total: 20, espaco_liberado_mb: 50, categoria: "Cache Chrome", categorias: [{nome: "Cache Chrome", status: "limpando", percentual: 50}] } };
            }
        };

        const execPromise = btn.onclick();
        
        await new Promise(r => setTimeout(r, 60)); // Let step 1 (progress) run
        
        const numerico = sandbox.document.getElementById('overlay-progresso-numerico');
        const categorias = sandbox.document.getElementById('overlay-categorias');
        assert(numerico.innerHTML.includes("10 / 20 itens"), "DOM: processados/total rendering");
        assert(numerico.innerHTML.includes("50 MB"), "DOM: liberado rendering");
        console.log("NUMERICO:", numerico.innerHTML);
        console.log("CATEGORIAS:", categorias.innerHTML);
        assert(categorias.innerHTML.includes("Cache Chrome"), "DOM: list rendering");
        const btnCancel = sandbox.document.getElementById('overlay-btn-cancelar');
        btnCancel.onclick();
        
        assert(btnCancel.disabled === true, "Botão desabilitado");
        assert(btnCancel.textContent === "Cancelando...", "Texto cancelando");
        assert(cancel_tarefa_calls === 1, "Chamou cancelar_tarefa");
        
        // Let polling run its course
        await execPromise;
        
        assert(cancel_tarefa_calls === 1, "Tarefa cancelada");
        console.log("verificar_tarefa_calls:", verificar_tarefa_calls);
        assert(verificar_tarefa_calls >= 2, "Polling continuou após abort até terminal");
        
        const container = sandbox.document.getElementById('conteudo-limpeza');
        assert(container.innerHTML.includes("Cancelado"), "Snapshot terminal renderizado (Cancelado)");
        assert(container.innerHTML.includes("10 itens processados"), "Snapshot terminal: itens");
        
        console.log("Todos os testes JS de limpeza (integração real) passaram.");
    } catch(e) {
        console.error(e);
        process.exit(1);
    }
}
runTests();
