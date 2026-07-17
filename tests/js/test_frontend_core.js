const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

// Mock browser environment
const window = {
    addEventListener: () => {},
    removeEventListener: () => {},
};
global.window = window;

const document = {
    getElementById: (id) => {
        if (id.startsWith('pagina-')) {
            return { classList: { add: () => {}, remove: () => {} } };
        }
        return null;
    },
    querySelectorAll: () => {
        return { forEach: (cb) => cb({ classList: { add: () => {}, remove: () => {} } }) };
    },
    querySelector: () => {
        return { classList: { add: () => {}, remove: () => {} } };
    }
};
global.document = document;
global.setTimeout = setTimeout;
global.setInterval = setInterval;
global.clearInterval = clearInterval;

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
let readyCb = null;
window.addEventListener = (ev, cb) => {
    if (ev === 'pywebviewready') readyCb = cb;
};
window.removeEventListener = (ev, cb) => {
    if (ev === 'pywebviewready') readyCb = null;
};
let promise = window.Phoenix.bridge.whenReady();
assert.strictEqual(window.Phoenix.bridge.isReady(), false);
window.pywebview = {
    api: {
        test_method: async (arg) => 'result_' + arg
    }
};
// trigger ready
readyCb();

promise.then(() => {
    assert.strictEqual(window.Phoenix.bridge.isReady(), true);
    
    // Test call()
    window.Phoenix.bridge.call('test_method', 'hello').then(res => {
        assert.strictEqual(res, 'result_hello');
    });

    // Test missing method
    window.Phoenix.bridge.call('missing').catch(err => {
        assert.ok(err.message.includes('não encontrado'));
    });
});

// 4. Lifecycle
loadScript('gui/js/core/lifecycle.js');
let count = 0;
window.Phoenix.lifecycle.setInterval('test_timer', () => { count++; }, 10);
setTimeout(() => {
    window.Phoenix.lifecycle.clearInterval('test_timer');
    let oldCount = count;
    setTimeout(() => {
        assert.strictEqual(count, oldCount, 'Timer should be stopped');
    }, 20);
}, 25);

// 5. Router
loadScript('gui/js/core/router.js');
let loadedPage = null;
window.Phoenix.router.setPageLoader((page) => { loadedPage = page; });
window.Phoenix.router.navigate('diagnostico');
assert.strictEqual(loadedPage, 'diagnostico');
assert.strictEqual(window.Phoenix.state.paginaAtual, 'diagnostico');

console.log("All native JS tests passed!");
