window.Phoenix = window.Phoenix || {};
window.Phoenix.ui = window.Phoenix.ui || {};

window.Phoenix.ui.icons = {
    create: function(name, options = {}) {
        const size = options.size || 24;
        const className = options.className || '';
        const decorative = options.decorative !== undefined ? options.decorative : true;
        const label = options.label || '';

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('stroke-width', '2');
        svg.setAttribute('stroke-linecap', 'round');
        svg.setAttribute('stroke-linejoin', 'round');
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        
        if (className) {
            svg.setAttribute('class', className);
        }

        if (decorative) {
            svg.setAttribute('aria-hidden', 'true');
        } else {
            svg.setAttribute('role', 'img');
            if (label) {
                svg.setAttribute('aria-label', label);
            } else {
                svg.setAttribute('aria-label', name);
            }
        }

        let paths = [];
        
        if (name === 'processando') {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', '12'); circle.setAttribute('cy', '12'); circle.setAttribute('r', '10');
            const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            polyline.setAttribute('points', '12 6 12 12 16 14');
            paths = [circle, polyline];
        } else if (name === 'sucesso') {
            svg.style.color = 'var(--cor-sucesso-texto, #4ade80)';
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', 'M22 11.08V12a10 10 0 1 1-5.93-9.14');
            const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            polyline.setAttribute('points', '22 4 12 14.01 9 11.01');
            paths = [path, polyline];
        } else if (name === 'aviso') {
            svg.style.color = 'var(--cor-alerta-texto, #facc15)';
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z');
            const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line1.setAttribute('x1', '12'); line1.setAttribute('y1', '9'); line1.setAttribute('x2', '12'); line1.setAttribute('y2', '13');
            const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line2.setAttribute('x1', '12'); line2.setAttribute('y1', '17'); line2.setAttribute('x2', '12.01'); line2.setAttribute('y2', '17');
            paths = [path, line1, line2];
        } else if (name === 'erro') {
            svg.style.color = 'var(--cor-erro-texto, #f87171)';
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', '12'); circle.setAttribute('cy', '12'); circle.setAttribute('r', '10');
            const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line1.setAttribute('x1', '15'); line1.setAttribute('y1', '9'); line1.setAttribute('x2', '9'); line1.setAttribute('y2', '15');
            const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line2.setAttribute('x1', '9'); line2.setAttribute('y1', '9'); line2.setAttribute('x2', '15'); line2.setAttribute('y2', '15');
            paths = [circle, line1, line2];
        } else if (name === 'informacao' || name === 'informação') {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', '12'); circle.setAttribute('cy', '12'); circle.setAttribute('r', '10');
            const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line1.setAttribute('x1', '12'); line1.setAttribute('y1', '16'); line1.setAttribute('x2', '12'); line1.setAttribute('y2', '12');
            const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line2.setAttribute('x1', '12'); line2.setAttribute('y1', '8'); line2.setAttribute('x2', '12.01'); line2.setAttribute('y2', '8');
            paths = [circle, line1, line2];
        } else if (name === 'usuario' || name === 'usuário') {
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2');
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', '12'); circle.setAttribute('cy', '7'); circle.setAttribute('r', '4');
            paths = [path, circle];
        } else if (name === 'excluir') {
            const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            polyline.setAttribute('points', '3 6 5 6 21 6');
            const path1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path1.setAttribute('d', 'M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2');
            const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line1.setAttribute('x1', '10'); line1.setAttribute('y1', '11'); line1.setAttribute('x2', '10'); line1.setAttribute('y2', '17');
            const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line2.setAttribute('x1', '14'); line2.setAttribute('y1', '11'); line2.setAttribute('x2', '14'); line2.setAttribute('y2', '17');
            paths = [polyline, path1, line1, line2];
        } else if (name === 'limpeza') {
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', 'M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6');
            paths = [path];
        } else if (name === 'otimizacao' || name === 'otimização') {
            const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            polygon.setAttribute('points', '13 2 3 14 12 14 11 22 21 10 12 10 13 2');
            paths = [polygon];
        } else if (name === 'diagnostico' || name === 'diagnóstico') {
            const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            polyline.setAttribute('points', '22 12 18 12 15 21 9 3 6 12 2 12');
            paths = [polyline];
        } else {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', '12'); circle.setAttribute('cy', '12'); circle.setAttribute('r', '10');
            const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line1.setAttribute('x1', '12'); line1.setAttribute('y1', '16'); line1.setAttribute('x2', '12'); line1.setAttribute('y2', '12');
            const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line2.setAttribute('x1', '12'); line2.setAttribute('y1', '8'); line2.setAttribute('x2', '12.01'); line2.setAttribute('y2', '8');
            paths = [circle, line1, line2];
        }

        paths.forEach(p => svg.appendChild(p));
        return svg;
    }
};
