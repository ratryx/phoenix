const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

// --- Mocking Environment ---
const window = {
    addEventListener: () => {},
    removeEventListener: () => {},
};
global.window = window;

const classes = new Set();
const style = { width: '', opacity: '' };
const classList = {
    add: (c) => classes.add(c),
    remove: (c) => classes.delete(c),
    contains: (c) => classes.has(c)
};
const elements = {};

const document = {
    getElementById: (id) => {
        if (!elements[id]) {
            elements[id] = { 
                id,
                classList, 
                style: { width: '', opacity: '' },
                textContent: '',
                addEventListener: () => {},
                removeEventListener: () => {}
            };
        }
        return elements[id];
    },
    querySelectorAll: () => {
        return { forEach: (cb) => cb({ classList, dataset: { pagina: 'teste' } }) };
    },
    querySelector: () => {
        return { classList };
    }
};
global.document = document;
global.setTimeout = setTimeout;
global.setInterval = setInterval;
global.clearInterval = clearInterval;
global.requestAnimationFrame = (cb) => setTimeout(cb, 16);
global.cancelAnimationFrame = clearTimeout;

function loadScript(filePath) {
    const code = fs.readFileSync(path.resolve(__dirname, '../../', filePath), 'utf8');
    vm.runInThisContext(code);
}

// 1. Namespace
loadScript('gui/js/core/namespace.js');
assert.ok(global.window.Phoenix, 'Phoenix namespace created');
loadScript('gui/js/core/namespace.js'); // double load
assert.ok(global.window.Phoenix, 'Phoenix namespace survives double load');

// 2. State
loadScript('gui/js/core/state.js');
assert.strictEqual(window.Phoenix.state.paginaAtual, 'inicio');
assert.strictEqual(window.Phoenix.state.nivelQualidadeVisual, 'medio');
assert.ok(window.Phoenix.state.intervalos, 'intervalos exists');

// 3. Bridge
loadScript('gui/js/core/bridge.js');
// Mock pywebview for whenReady
let readyCbs = [];
window.addEventListener = (ev, cb) => {
    if (ev === 'pywebviewready') readyCbs.push(cb);
};
window.removeEventListener = (ev, cb) => {
    if (ev === 'pywebviewready') readyCbs = readyCbs.filter(c => c !== cb);
};

// Scenario: API indisponível
let promise1 = window.Phoenix.bridge.whenReady();
let promise2 = window.Phoenix.bridge.whenReady();
assert.strictEqual(promise1, promise2, 'Duas chamadas devem retornar a mesma promise');
assert.strictEqual(window.Phoenix.bridge.isReady(), false);

// Scenario: Disponibilizada depois do registro
window.pywebview = {
    api: {
        test_method: async (arg) => 'result_' + arg
    }
};
readyCbs.forEach(cb => cb());

promise1.then(() => {
    assert.strictEqual(window.Phoenix.bridge.isReady(), true);
    
    // Test call() - Argumentos repassados e this não perdido
    window.Phoenix.bridge.call('test_method', 'hello').then(res => {
        assert.strictEqual(res, 'result_hello');
    });

    // Test missing method
    window.Phoenix.bridge.call('missing').catch(err => {
        assert.ok(err.message.includes('não encontrado'));
    });
    
    // Scenario: API já disponível antes de whenReady() posterior
    window.Phoenix.bridge.whenReady().then(() => {
        assert.ok(true, 'Deve resolver imediatamente');
    });
});

// 4. Jobs
loadScript('gui/js/core/jobs.js');
// Mock api
let checkCount = 0;
window.pywebview.api.verificar_tarefa = async (jobId) => {
    checkCount++;
    if (jobId === 'running') return { status: 'running', progresso: 50, mensagem: 'msg' };
    if (jobId === 'done') return { status: 'done', resultado: { ok: true, data: 'ok' } };
    if (jobId === 'done_false') return { status: 'done', resultado: { ok: false } };
    if (jobId === 'not_found') return { status: 'not_found' };
    if (jobId === 'timeout') return { status: 'running' }; // forces timeout eventually
    if (jobId === 'error') throw new Error('Bridge err');
};

(async function testJobs() {
    // done
    let res = await window.Phoenix.jobs.awaitJob('done');
    assert.deepStrictEqual(res, { ok: true, data: 'ok' });

    // done_false
    res = await window.Phoenix.jobs.awaitJob('done_false');
    assert.deepStrictEqual(res, { ok: false });

    // not_found
    try {
        await window.Phoenix.jobs.awaitJob('not_found');
        assert.fail('Should reject');
    } catch (e) {
        assert.ok(e.message.includes('não encontrado'));
    }

    // error
    try {
        await window.Phoenix.jobs.awaitJob('error');
        assert.fail('Should reject');
    } catch (e) {
        assert.ok(e.message.includes('Bridge err'));
    }

    // timeout
    // Redefinindo constante MAX_TENTATIVAS para o teste ser rápido (mockando setTimeout na funcao)
    const oldSetTimeout = global.setTimeout;
    let timeouts = 0;
    global.setTimeout = (cb, ms) => {
        timeouts++;
        if (timeouts > 130) {
            assert.fail('Loop infinito');
        }
        oldSetTimeout(cb, 1);
    };
    try {
        await window.Phoenix.jobs.awaitJob('timeout');
        assert.fail('Should timeout');
    } catch (e) {
        assert.ok(e.message.includes('Timeout'));
    }
    global.setTimeout = oldSetTimeout;

    // progresso
    let p = 0;
    let original_verificar_tarefa = window.pywebview.api.verificar_tarefa;
    window.pywebview.api.verificar_tarefa = async (jobId) => {
        if (jobId === 'prog') {
            p++;
            if (p === 1) return { status: 'running', progresso: 50, mensagem: 'msg' };
            return { status: 'done', resultado: 'done' };
        }
        return original_verificar_tarefa(jobId);
    };
    let progArgs = null;
    await window.Phoenix.jobs.awaitJob('prog', (prog, msg) => {
        progArgs = { prog, msg };
    });
    assert.deepStrictEqual(progArgs, { prog: 50, msg: 'msg' });

    // test independent calls
    let j1 = window.Phoenix.jobs.awaitJob('done');
    let j2 = window.Phoenix.jobs.awaitJob('done_false');
    let [r1, r2] = await Promise.all([j1, j2]);
    assert.deepStrictEqual(r1, { ok: true, data: 'ok' });
    assert.deepStrictEqual(r2, { ok: false });
})();

// 5. Lifecycle
loadScript('gui/js/core/lifecycle.js');
let lc_count = 0;
window.Phoenix.lifecycle.setInterval('test_timer', () => { lc_count++; }, 10);
setTimeout(() => {
    window.Phoenix.lifecycle.clearInterval('test_timer');
    let oldCount = lc_count;
    setTimeout(() => {
        assert.strictEqual(lc_count, oldCount, 'Timer should be stopped');
    }, 20);
}, 25);
window.Phoenix.lifecycle.setInterval('test2', () => {}, 10);
window.Phoenix.lifecycle.clearAll();
assert.strictEqual(Object.keys(window.Phoenix.lifecycle._timers || {}).length, 0);

// 6. Router
loadScript('gui/js/core/router.js');
let loadedPage = null;
window.Phoenix.router.setPageLoader((page) => { loadedPage = page; });
window.Phoenix.router.navigate('diagnostico');
assert.strictEqual(loadedPage, 'diagnostico');
assert.strictEqual(window.Phoenix.state.paginaAtual, 'diagnostico');

// 7. Feedback
loadScript('gui/js/ui/feedback.js');
window.Phoenix.ui.feedback.mostrarOverlay('Teste');
assert.strictEqual(document.getElementById('overlay-texto').textContent, 'Teste');
window.Phoenix.ui.feedback.esconderOverlay();

window.Phoenix.ui.feedback.mostrarOverlay('Destrutivo', true);
assert.ok(classes.has('visivel'));
window.Phoenix.ui.feedback.atualizarOverlay('Novo Status', 50);
assert.strictEqual(document.getElementById('overlay-status').textContent, 'Novo Status');
assert.strictEqual(document.getElementById('overlay-barra-fill').style.width, '50%');

window.Phoenix.ui.feedback.esconderOverlay(true, false);
setTimeout(() => {
    assert.ok(!classes.has('visivel'), 'Overlay deve ser fechado');
    console.log("All native JS tests passed!");
}, 1500);

// Modal
let modalPromise = window.Phoenix.ui.feedback.confirmarModal('T', 'M');
setTimeout(() => {
    document.getElementById('btn-modal-confirm-ok').dispatchEvent = true; // fake
}, 10);
