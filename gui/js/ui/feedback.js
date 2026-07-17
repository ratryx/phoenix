(function (Phoenix) {
    "use strict";

    var _barraProgresso = null;

    Phoenix.ui.feedback.mostrarOverlay = function(texto, destrutivo = false) {
        if (!destrutivo) {
            // Barra de progresso fina no topo
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
        
        // Overlay destrutivo com card de progresso
        const overlay = document.getElementById('overlay-processando');
        const titulo = document.getElementById('overlay-titulo');
        const subtitulo = document.getElementById('overlay-subtitulo');
        const barraFill = document.getElementById('overlay-barra-fill');
        const status = document.getElementById('overlay-status');
        const icone = document.getElementById('overlay-icone');
        
        if (titulo) titulo.textContent = texto || 'Processando...';
        if (subtitulo) subtitulo.textContent = 'Aguarde, isso pode levar alguns segundos';
        if (status) status.textContent = 'Iniciando...';
        if (icone) icone.textContent = '⚙️';
        
        // Inicia animação indeterminada
        if (barraFill) {
            barraFill.classList.add('indeterminado');
            barraFill.style.width = '';
        }
        
        if (overlay) overlay.classList.add('visivel');
    };

    Phoenix.ui.feedback.atualizarOverlay = function(texto, percentual = null) {
        const status = document.getElementById('overlay-status');
        const barraFill = document.getElementById('overlay-barra-fill');
        
        if (status) status.textContent = texto;
        
        if (percentual !== null && barraFill) {
            barraFill.classList.remove('indeterminado');
            barraFill.style.width = percentual + '%';
        }
    };

    Phoenix.ui.feedback.esconderOverlay = function(destrutivo = false, sucesso = true) {
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
        
        // Mostrar conclusão antes de fechar
        if (barraFill) {
            barraFill.classList.remove('indeterminado');
            barraFill.style.width = '100%';
        }
        if (icone) icone.textContent = sucesso ? '✅' : '⚠️';
        if (titulo) titulo.textContent = sucesso ? 'Concluído!' : 'Atenção';
        if (status) status.textContent = sucesso ? 'Operação finalizada com sucesso' : 'Verifique os resultados';
        
        setTimeout(() => {
            if (overlay) overlay.classList.remove('visivel');
            // Reset para próxima vez
            setTimeout(() => {
                if (barraFill) {
                    barraFill.style.width = '0%';
                    barraFill.classList.remove('indeterminado');
                }
            }, 300);
        }, 1200);
    };

    Phoenix.ui.feedback.confirmarModal = function(titulo, mensagem, icone = '⚠️') {
        return new Promise((resolve) => {
            const modal = document.getElementById('modal-confirmacao');
            const tituloEl = document.getElementById('modal-confirm-titulo');
            const mensagemEl = document.getElementById('modal-confirm-mensagem');
            const iconeEl = document.getElementById('modal-confirm-icone');
            const btnOk = document.getElementById('btn-modal-confirm-ok');
            const btnCancelar = document.getElementById('btn-modal-confirm-cancelar');
            
            if (tituloEl) tituloEl.textContent = titulo;
            if (mensagemEl) mensagemEl.textContent = mensagem;
            if (iconeEl) iconeEl.textContent = icone;
            
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

    // Globais temporários 
    window.mostrarOverlay = Phoenix.ui.feedback.mostrarOverlay;
    window.esconderOverlay = Phoenix.ui.feedback.esconderOverlay;

})(window.Phoenix);
