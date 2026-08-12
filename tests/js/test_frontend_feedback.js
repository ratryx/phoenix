const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const scriptPath = path.join(__dirname, '..', '..', 'gui', 'js', 'ui', 'feedback.js');
const scriptCode = fs.readFileSync(scriptPath, 'utf8');

function setupEnvironment() {
    const context = {
        window: {},
        document: {
            getElementById: function (id) {
                if (!context.elements[id]) {
                    context.elements[id] = {
                        id: id,
                        className: '',
                        classList: {
                            add: function(c) {
                                let classes = context.elements[id].className.split(' ').filter(x => x);
                                if (!classes.includes(c)) {
                                    classes.push(c);
                                    context.elements[id].className = classes.join(' ');
                                }
                            },
                            remove: function(c) {
                                let classes = context.elements[id].className.split(' ').filter(x => x);
                                context.elements[id].className = classes.filter(x => x !== c).join(' ');
                            },
                            contains: function(c) {
                                return context.elements[id].className.split(' ').filter(x => x).includes(c);
                            }
                        },
                        style: {},
                        children: [],
                        textContent: '',
                        appendChild: function(c) { this.children.push(c); },
                        replaceChildren: function() { this.children = []; },
                        firstChild: null,
                        removeChild: function() {}
                    };
                }
                return context.elements[id];
            },
            createElement: function(tag) { return { tagName: tag, style: {}, classList: { add: function(){}, remove: function(){} } }; },
            createTextNode: function(t) { return { textContent: t }; }
        },
        console: {
            error: function () { context.errors.push(Array.from(arguments)); },
            log: function () { context.logs.push(Array.from(arguments)); }
        },
        Phoenix: { 
            ui: { 
                icons: { create: function() { return {}; } },
                feedback: {}
            }
        },
        setTimeout: function(cb, delay) {
            const id = context.timerId++;
            context.timers.push({ id, cb, delay });
            return id;
        },
        clearTimeout: function(id) {
            context.timers = context.timers.filter(t => t.id !== id);
        }
    };
    context.window.Phoenix = context.Phoenix;
    context.elements = {};
    context.errors = [];
    context.logs = [];
    context.timers = [];
    context.timerId = 1;

    context.advanceTimers = function(ms) {
        let toRun = context.timers.filter(t => t.delay <= ms);
        context.timers = context.timers.filter(t => t.delay > ms);
        toRun.forEach(t => t.cb());
    };

    vm.createContext(context);
    vm.runInContext(scriptCode, context);

    return context;
}

async function runTests() {
    console.log("Iniciando testes Feedback (Overlay Race)...");

    const ctx = setupEnvironment();
    
    // show overlay A
    ctx.Phoenix.ui.feedback.mostrarOverlay("Overlay A", true);
    
    // Simulate it becoming visible
    ctx.document.getElementById('overlay-processando').classList.add('visivel');
    
    // hide overlay A (delayed)
    ctx.Phoenix.ui.feedback.esconderOverlay(true);
    
    // Before the 1200ms timeout fires, show overlay B
    ctx.Phoenix.ui.feedback.mostrarOverlay("Overlay B", true);
    
    // advance timers by 2000ms
    ctx.advanceTimers(2000);
    
    // overlay B MUST remain visible (visivel class should still be there)
    const overlay = ctx.document.getElementById('overlay-processando');
    assert.ok(overlay.classList.contains('visivel'), "Overlay B MUST remain visible, hide race condition failed");
    
    // Normal hide should work
    ctx.Phoenix.ui.feedback.esconderOverlay(true);
    ctx.advanceTimers(2000);
    assert.ok(!overlay.classList.contains('visivel'), "Normal hide should remove visivel class");
    
    console.log("Testes JS Feedback (Overlay Race) passaram.");
}

runTests().catch(err => {
    console.error("Falha nos testes:", err);
    process.exit(1);
});
