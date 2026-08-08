const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function runTests() {
    const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'pages', 'servicos.js');
    const scriptCode = fs.readFileSync(scriptPath, 'utf8');

    const sandbox = {
        window: {
            Phoenix: {
                bridge: { call: async () => ({ job_id: '123' }) },
                jobs: { awaitJob: async () => ({ ok: true }) },
                ui: {
                    feedback: {
                        mostrarOverlay: () => {},
                        esconderOverlay: () => {}
                    }
                },
                operations: {
                    restorePoint: {
                        runProtected: async (fn) => {
                            sandbox.lastRunProtected = fn();
                            await sandbox.lastRunProtected;
                        }
                    }
                },
                pages: {}
            },
            document: {
                getElementById: (id) => {
                    return sandbox.mockDom[id] || null;
                },
                createElement: (tag) => {
                    const el = { tag: tag, children: [], dataset: {}, classList: {
                        classes: [],
                        toggle: function(c) {
                            const idx = this.classes.indexOf(c);
                            if(idx > -1) this.classes.splice(idx, 1);
                            else this.classes.push(c);
                        }
                    }, style: {} };
                    Object.defineProperty(el, 'className', {
                        get: function() { return this.classList.classes.join(' '); },
                        set: function(v) { this.classList.classes = v.split(' '); }
                    });
                    el.appendChild = function(c) { this.children.push(c); };
                    el.addEventListener = function(ev, cb) {
                        if(!this.listeners) this.listeners = {};
                        this.listeners[ev] = cb;
                    };
                    return el;
                },
                createTextNode: (text) => text
            }
        },
        console: { error: () => {}, log: () => {} },
        mockDom: {
            'conteudo-servicos': { 
                children: [], 
                innerHTML: '',
                appendChild: function(c) { this.children.push(c); },
                querySelectorAll: function(sel) {
                    if (sel === '.toggle') {
                        // find all toggles in the tree
                        let toggles = [];
                        function traverse(node) {
                            if(node && node.classList && node.classList.classes.includes('toggle')) toggles.push(node);
                            if(node && node.children) node.children.forEach(traverse);
                        }
                        this.children.forEach(traverse);
                        return toggles;
                    }
                    return [];
                }
            },
            'btn-atualizar-servicos': { dataset: {}, addEventListener: (ev, cb) => { sandbox.refreshCb = cb; } }
        }
    };

    sandbox.document = sandbox.window.document;
    sandbox.Phoenix = sandbox.window.Phoenix;

    vm.createContext(sandbox);
    vm.runInContext(scriptCode, sandbox);

    (async () => {
        try {
            // Test 1: Load and render
            sandbox.Phoenix.jobs.awaitJob = async () => ({
                ok: true,
                servicos: [
                    { nome_servico: "SvcRunning", nome_amigavel: "Svc 1", descricao: "D1", status: "Rodando", managed_by_phoenix: false },
                    { nome_servico: "SvcStopped", nome_amigavel: "Svc 2", descricao: "D2", status: "Parado", managed_by_phoenix: false },
                    { nome_servico: "SvcManaged", nome_amigavel: "Svc 3", descricao: "D3", status: "Parado", managed_by_phoenix: true }
                ]
            });

            await sandbox.Phoenix.pages.servicos.load();
            const toggles = sandbox.mockDom['conteudo-servicos'].querySelectorAll('.toggle');
            assert(toggles.length === 3, "Devem existir 3 toggles");

            const btnRunning = toggles.find(t => t.dataset.servico === 'SvcRunning');
            const btnStopped = toggles.find(t => t.dataset.servico === 'SvcStopped');
            const btnManaged = toggles.find(t => t.dataset.servico === 'SvcManaged');

            assert(btnRunning.dataset.ativo === 'true', 'SvcRunning is ativo');
            assert(btnRunning.dataset.gerenciado === 'false', 'SvcRunning not managed');
            
            assert(btnStopped.dataset.ativo === 'false', 'SvcStopped is not ativo');
            assert(btnStopped.dataset.gerenciado === 'false', 'SvcStopped not managed');

            assert(btnManaged.dataset.ativo === 'false', 'SvcManaged is not ativo');
            assert(btnManaged.dataset.gerenciado === 'true', 'SvcManaged is managed');

            // B. RUNNING unmanaged service: click -> desativar_servico
            let endpointCalled = null;
            let payloadCalled = null;
            sandbox.Phoenix.bridge.call = async (ep, arg) => { endpointCalled = ep; payloadCalled = arg; return { job_id: '123' }; };
            
            btnRunning.listeners['click']();
            await sandbox.lastRunProtected;
            
            assert(endpointCalled === 'desativar_servico', "Deve chamar desativar_servico");
            assert(payloadCalled === 'SvcRunning');
            // E. after successful disable: local toggle managed flag becomes true
            assert(btnRunning.dataset.ativo === 'false', "Deve ficar inativo");
            assert(btnRunning.dataset.gerenciado === 'true', "Deve ficar gerenciado");

            // C. STOPPED unmanaged service: click -> iniciar_servico
            endpointCalled = null; payloadCalled = null;
            btnStopped.listeners['click']();
            await sandbox.lastRunProtected;
            
            assert(endpointCalled === 'iniciar_servico', "Deve chamar iniciar_servico");
            assert(payloadCalled === 'SvcStopped');
            assert(btnStopped.dataset.ativo === 'true', "Deve ficar ativo");
            assert(btnStopped.dataset.gerenciado === 'false', "Ainda não gerenciado (foi só iniciado)");

            // D. STOPPED managed_by_phoenix service: click -> restaurar_servico
            endpointCalled = null; payloadCalled = null;
            btnManaged.listeners['click']();
            await sandbox.lastRunProtected;
            
            assert(endpointCalled === 'restaurar_servico', "Deve chamar restaurar_servico");
            assert(payloadCalled === 'SvcManaged');
            // F. after successful restore: local managed flag becomes false
            assert(btnManaged.dataset.ativo === 'true', "Deve ficar ativo");
            assert(btnManaged.dataset.gerenciado === 'false', "Perde flag gerenciado");

            // G. double-click protection
            let callCount = 0;
            sandbox.Phoenix.bridge.call = async (ep, arg) => { callCount++; return { job_id: '123' }; };
            // btnManaged is now ativo=true. Let's click it twice simultaneously
            btnManaged.listeners['click']();
            const p1 = sandbox.lastRunProtected;
            btnManaged.listeners['click']();
            const p2 = sandbox.lastRunProtected;
            await Promise.all([p1, p2]);
            assert(callCount === 1, "Proteção contra duplo clique deve funcionar");

            console.log("Todos os testes JS da Página Serviços passaram.");
        } catch(e) {
            console.error(e);
            process.exit(1);
        }
    })();
}

runTests();
