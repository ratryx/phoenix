(function (Phoenix) {
    "use strict";

    var _barraProgresso = null;


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
            icone.appendChild(Phoenix.ui.icons.create('processando'));
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
            icone.appendChild(Phoenix.ui.icons.create(iconName));
        }
        
        if (titulo) titulo.textContent = sucesso ? (parcial ? 'Concluído (Parcial)' : 'Concluído!') : 'Atenção';
        if (status && !sucesso) {
            status.textContent = 'Verifique os resultados';
        } else if (status) {
            status.textContent = 'Operação finalizada';
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
                iconeEl.appendChild(Phoenix.ui.icons.create(iconeName));
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

