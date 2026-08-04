(function (Phoenix) {
    "use strict";

    var _barraProgresso = null;

        Phoenix.ui.icons = {
        createSVG: function(name) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('viewBox', '0 0 24 24');
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', 'currentColor');
            svg.setAttribute('stroke-width', '2');
            svg.setAttribute('stroke-linecap', 'round');
            svg.setAttribute('stroke-linejoin', 'round');
            svg.setAttribute('width', '24');
            svg.setAttribute('height', '24');

            if (name === 'processando') {
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', '12'); circle.setAttribute('cy', '12'); circle.setAttribute('r', '10');
                const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
                polyline.setAttribute('points', '12 6 12 12 16 14');
                svg.appendChild(circle); svg.appendChild(polyline);
            } else if (name === 'sucesso') {
                svg.style.color = 'var(--cor-sucesso-texto, #4ade80)';
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', 'M22 11.08V12a10 10 0 1 1-5.93-9.14');
                const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
                polyline.setAttribute('points', '22 4 12 14.01 9 11.01');
                svg.appendChild(path); svg.appendChild(polyline);
            } else if (name === 'erro') {
                svg.style.color = 'var(--cor-erro-texto, #f87171)';
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', '12'); circle.setAttribute('cy', '12'); circle.setAttribute('r', '10');
                const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line1.setAttribute('x1', '15'); line1.setAttribute('y1', '9'); line1.setAttribute('x2', '9'); line1.setAttribute('y2', '15');
                const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line2.setAttribute('x1', '9'); line2.setAttribute('y1', '9'); line2.setAttribute('x2', '15'); line2.setAttribute('y2', '15');
                svg.appendChild(circle); svg.appendChild(line1); svg.appendChild(line2);
            } else { // aviso
                svg.style.color = 'var(--cor-alerta-texto, #facc15)';
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z');
                const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line1.setAttribute('x1', '12'); line1.setAttribute('y1', '9'); line1.setAttribute('x2', '12'); line1.setAttribute('y2', '13');
                const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line2.setAttribute('x1', '12'); line2.setAttribute('y1', '17'); line2.setAttribute('x2', '12.01'); line2.setAttribute('y2', '17');
                svg.appendChild(path); svg.appendChild(line1); svg.appendChild(line2);
            }
            return svg;
        }
    };

    Phoenix.ui.feedback.mostrarOverlay = function(texto, destrutivo = false) {
        if (!destrutivo) {
            const barra = document.getElementById('barra-progresso-global');
            const fill = document.getElementById('barra-progresso-fill');
            const textoEl = document.getElementById('overlay-texto');
            if (barra) barra.style.opacity = '1';
            if (textoEl) { 
                textoEl.textContent = texto || 'Carregando...'; 
                textoEl.style.opacity = '1'; 
            }
            if (fill) {
                fill.style.width = '0%';
                setTimeout(() => { if (fill) fill.style.width = '60%'; }, 50);
                setTimeout(() => { if (fill) fill.style.width = '80%'; }, 500);
            }
            _barraProgresso = { barra, fill, textoEl };
            return;
        }
        
        const overlay = document.getElementById('overlay-processando');
        const titulo = document.getElementById('overlay-titulo');
        const subtitulo = document.getElementById('overlay-subtitulo');
        const barraFill = document.getElementById('overlay-barra-fill');
        const status = document.getElementById('overlay-status');
        const icone = document.getElementById('overlay-icone');
        
        if (titulo) titulo.textContent = texto || 'Processando...';
        if (subtitulo) subtitulo.textContent = 'Aguarde, isso pode levar alguns segundos';
        if (status) status.textContent = 'Iniciando...';
        if (icone) {
            while (icone.firstChild) { icone.removeChild(icone.firstChild); }
            icone.appendChild(Phoenix.ui.icons.createSVG('processando'));
        }
        
        if (barraFill) {
            barraFill.classList.add('indeterminado');
            barraFill.style.width = '';
        }
        
        if (overlay) overlay.classList.add('visivel');
    };

    Phoenix.ui.feedback.atualizarOverlay = function(texto, percentual = null, detalhes = null) {
        const status = document.getElementById('overlay-status');
        const barraFill = document.getElementById('overlay-barra-fill');
        
        if (status) status.textContent = texto;
        
        if (percentual !== null && barraFill) {
            barraFill.classList.remove('indeterminado');
            barraFill.style.width = percentual + '%';
        }
        
        const subtitulo = document.getElementById('overlay-subtitulo');
        if (detalhes && subtitulo) {
            let info = [];
            if (detalhes.categoria) info.push(`Categoria: ${detalhes.categoria}`);
            if (detalhes.arquivos_processados !== undefined) info.push(`Arquivos: ${detalhes.arquivos_processados}`);
            if (detalhes.espaco_liberado_mb !== undefined) info.push(`Liberado: ${detalhes.espaco_liberado_mb} MB`);
            if (info.length > 0) {
                subtitulo.textContent = info.join(" | ");
            }
        }
    };

    Phoenix.ui.feedback.esconderOverlay = function(destrutivo = false, sucesso = true, parcial = false) {
        if (!destrutivo) {
            if (_barraProgresso) {
                const { barra, fill, textoEl } = _barraProgresso;
                if (fill) fill.style.width = '100%';
                setTimeout(() => {
                    if (barra) barra.style.opacity = '0';
                    if (textoEl) textoEl.style.opacity = '0';
                    setTimeout(() => { if (fill) fill.style.width = '0%'; }, 300);
                }, 300);
                _barraProgresso = null;
            }
            return;
        }
        
        const overlay = document.getElementById('overlay-processando');
        const barraFill = document.getElementById('overlay-barra-fill');
        const titulo = document.getElementById('overlay-titulo');
        const icone = document.getElementById('overlay-icone');
        const status = document.getElementById('overlay-status');
        
        if (barraFill) {
            barraFill.classList.remove('indeterminado');
            barraFill.style.width = '100%';
        }
        
        let iconName = sucesso ? (parcial ? 'aviso' : 'sucesso') : 'erro';
        if (icone) {
            while (icone.firstChild) { icone.removeChild(icone.firstChild); }
            icone.appendChild(Phoenix.ui.icons.createSVG(iconName));
        }
        
        if (titulo) titulo.textContent = sucesso ? (parcial ? 'ConcluÃ­do (Parcial)' : 'ConcluÃ­do!') : 'AtenÃ§Ã£o';
        if (status && !sucesso) {
            status.textContent = 'Verifique os resultados';
        } else if (status) {
            status.textContent = 'OperaÃ§Ã£o finalizada';
        }
        
        setTimeout(() => {
            if (overlay) overlay.classList.remove('visivel');
            setTimeout(() => {
                if (barraFill) {
                    barraFill.style.width = '0%';
                    barraFill.classList.remove('indeterminado');
                }
            }, 300);
        }, 1200);
    };

    Phoenix.ui.feedback.confirmarModal = function(titulo, mensagem, iconeName = 'aviso') {
        return new Promise((resolve) => {
            const modal = document.getElementById('modal-confirmacao');
            const tituloEl = document.getElementById('modal-confirm-titulo');
            const mensagemEl = document.getElementById('modal-confirm-mensagem');
            const iconeEl = document.getElementById('modal-confirm-icone');
            const btnOk = document.getElementById('btn-modal-confirm-ok');
            const btnCancelar = document.getElementById('btn-modal-confirm-cancelar');
            
            if (tituloEl) tituloEl.textContent = titulo;
            if (mensagemEl) mensagemEl.textContent = mensagem;
            if (iconeEl) {
                while (iconeEl.firstChild) { iconeEl.removeChild(iconeEl.firstChild); }
                iconeEl.appendChild(Phoenix.ui.icons.createSVG(iconeName));
            }
            
            modal.classList.add('visivel');
            
            const fechar = (resultado) => {
                modal.classList.remove('visivel');
                btnOk.removeEventListener('click', onOk);
                btnCancelar.removeEventListener('click', onCancelar);
                resolve(resultado);
            };
            
            const onOk = () => fechar(true);
            const onCancelar = () => fechar(false);
            
            btnOk.addEventListener('click', onOk);
            btnCancelar.addEventListener('click', onCancelar);
        });
    };

    Phoenix.ui.corPorPercentual = function(pct) {
        if (pct >= 90) return "erro";
        if (pct >= 70) return "alerta";
        return "";
    };

    window.mostrarOverlay = Phoenix.ui.feedback.mostrarOverlay;
    window.esconderOverlay = Phoenix.ui.feedback.esconderOverlay;

})(window.Phoenix);

