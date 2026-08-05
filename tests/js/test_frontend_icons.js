const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

class MockElement {
    constructor(tag) {
        this.tag = tag;
        this.attributes = {};
        this.children = [];
        this.style = {};
    }
    setAttribute(name, value) {
        this.attributes[name] = value;
    }
    getAttribute(name) {
        return this.attributes[name];
    }
    appendChild(child) {
        this.children.push(child);
    }
    querySelectorAll(selectors) {
        const parts = selectors.split(',').map(s => s.trim());
        let results = [];
        for (let child of this.children) {
            if (parts.includes(child.tag)) results.push(child);
            results = results.concat(child.querySelectorAll(selectors));
        }
        return results;
    }
}

const windowObj = { Phoenix: { ui: {} } };
const mockDoc = {
    createElementNS: function(ns, tag) {
        return new MockElement(tag);
    }
};

const context = vm.createContext({
    window: windowObj,
    document: mockDoc
});

const iconsPath = path.join(__dirname, '../../gui/js/ui/icons.js');
const iconsCode = fs.readFileSync(iconsPath, 'utf8');
vm.runInContext(iconsCode, context);

function testIcons() {
    let failed = false;
    const P = context.window.Phoenix;
    
    let svg = P.ui.icons.create('qualquer_coisa_inexistente');
    let paths = svg.querySelectorAll('circle, line');
    if (paths.length !== 3) {
        console.error("FALHOU: Ícone desconhecido não retornou fallback de informação");
        failed = true;
    }

    let decSvg = P.ui.icons.create('sucesso', { decorative: true });
    if (decSvg.getAttribute('aria-hidden') !== 'true') {
        console.error("FALHOU: Ícone decorativo sem aria-hidden");
        failed = true;
    }
    
    let infoSvg = P.ui.icons.create('informacao', { decorative: false });
    if (infoSvg.getAttribute('role') !== 'img') {
        console.error("FALHOU: Ícone informativo sem role=img");
        failed = true;
    }
    if (infoSvg.getAttribute('aria-label') !== 'informacao') {
        console.error("FALHOU: Ícone informativo sem label padrão. Got: " + infoSvg.getAttribute('aria-label'));
        failed = true;
    }

    if (iconsCode.includes('innerHTML')) {
        console.error("FALHOU: icons.js contém innerHTML");
        failed = true;
    }
    if (!iconsCode.includes('createElementNS')) {
        console.error("FALHOU: icons.js não usa createElementNS");
        failed = true;
    }

    if (failed) {
        process.exit(1);
    } else {
        console.log("Todos os testes de ícones passaram.");
    }
}

testIcons();
