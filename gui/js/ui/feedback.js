(function (Phoenix) {

    "use strict";



    var _barraProgresso = null;
    var _hideTimeout = null;





    Phoenix.ui.feedback.mostrarOverlay = function(texto, opcoes = {}) {
        let destrutivo = false;
        let cancelavel = false;
        if (typeof opcoes === 'boolean') {
            destrutivo = opcoes;
        } else if (opcoes && typeof opcoes === 'object') {
            destrutivo = opcoes.destrutivo || false;
            cancelavel = opcoes.cancelavel || false;
        }

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

        if (_hideTimeout) {
            clearTimeout(_hideTimeout);
            _hideTimeout = null;
        }

        const overlay = document.getElementById('overlay-processando');
        const titulo = document.getElementById('overlay-titulo');
        const subtitulo = document.getElementById('overlay-subtitulo');
        const barraFill = document.getElementById('overlay-barra-fill');
        const status = document.getElementById('overlay-status');
        const icone = document.getElementById('overlay-icone');
        const faseBadge = document.getElementById('overlay-fase-badge');
        const stepper = document.getElementById('overlay-stepper');
        const painelAtiv = document.getElementById('overlay-painel-atividade');

        if (titulo) titulo.textContent = texto || 'Processando...';
        if (subtitulo) subtitulo.textContent = 'Aguarde, isso pode levar alguns minutos...';
        if (status) status.textContent = 'Iniciando...';
        if (icone) {
            while (icone.firstChild) { icone.removeChild(icone.firstChild); }
            icone.appendChild(Phoenix.ui.icons.create('processando'));
            icone.style.display = 'block';
        }

        if (barraFill) {
            barraFill.classList.add('indeterminado');
            barraFill.style.width = '0%';
        }

        const isRotina = (texto || '').toLowerCase().includes('rotina');
        if (isRotina) {
            if (faseBadge) {
                faseBadge.style.display = 'block';
                faseBadge.textContent = 'Fase 1/4';
            }
            if (stepper) {
                stepper.style.display = 'flex';
                stepper.innerHTML = `
                    <div class="stepper-fase ativa" data-fase="1">
                        <div class="stepper-fase-ponto"></div>
                        <div class="stepper-fase-rotulo">Preparo</div>
                    </div>
                    <div class="stepper-fase" data-fase="2">
                        <div class="stepper-fase-ponto"></div>
                        <div class="stepper-fase-rotulo">Limpeza</div>
                    </div>
                    <div class="stepper-fase" data-fase="3">
                        <div class="stepper-fase-ponto"></div>
                        <div class="stepper-fase-rotulo">Otimização</div>
                    </div>
                    <div class="stepper-fase" data-fase="4">
                        <div class="stepper-fase-ponto"></div>
                        <div class="stepper-fase-rotulo">Finalizando</div>
                    </div>
                `;
            }
        } else {
            if (faseBadge) faseBadge.style.display = 'none';
            if (stepper) stepper.style.display = 'none';
        }

        const detalhesContainer = document.getElementById('overlay-detalhes-limpeza');
        if (detalhesContainer) {
            detalhesContainer.style.display = 'none';
        }
        if (painelAtiv) painelAtiv.style.display = 'none';

        const categoriasLista = document.getElementById('overlay-categorias');
        if (categoriasLista) categoriasLista.replaceChildren();

        const btnCancelar = document.getElementById('overlay-btn-cancelar');
        if (btnCancelar) {
            if (cancelavel) {
                btnCancelar.disabled = false;
                btnCancelar.textContent = 'Cancelar';
                btnCancelar.style.display = 'inline-block';
            } else {
                btnCancelar.style.display = 'none';
            }
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
            
            // Stepper logic
            const txt = (texto || '').toLowerCase();
            let fase = 1;
            if (txt.includes('limpeza') || txt.includes('limpando') || percentual >= 10 && percentual < 45) fase = 2;
            else if (txt.includes('otimiz') || txt.includes('inicialização') || txt.includes('smart') || percentual >= 45 && percentual < 85) fase = 3;
            else if (txt.includes('relatório') || percentual >= 85) fase = 4;
            
            const faseBadge = document.getElementById('overlay-fase-badge');
            if (faseBadge && faseBadge.style.display !== 'none') {
                faseBadge.textContent = `Fase ${fase}/4`;
                const steppers = document.querySelectorAll('.stepper-fase');
                steppers.forEach(el => {
                    const f = parseInt(el.getAttribute('data-fase'), 10);
                    if (f < fase) { el.classList.remove('ativa'); el.classList.add('concluida'); }
                    else if (f === fase) { el.classList.add('ativa'); el.classList.remove('concluida'); }
                    else { el.classList.remove('ativa'); el.classList.remove('concluida'); }
                });
            }
        }

        const subtitulo = document.getElementById('overlay-subtitulo');
        const detalhesContainer = document.getElementById('overlay-detalhes-limpeza');
        
        if (detalhes && detalhes.categorias) {
            if (detalhesContainer) detalhesContainer.style.display = 'block';
            
            const pNum = document.getElementById('overlay-progresso-numerico');
            const rEsp = document.getElementById('overlay-resumo-espaco');
            const painelAtiv = document.getElementById('overlay-painel-atividade');
            if (painelAtiv) painelAtiv.style.display = 'block';

            let proc = detalhes.arquivos_processados || 0;
            let tot = detalhes.arquivos_total || 0;
            let lib = detalhes.espaco_liberado_mb !== undefined ? detalhes.espaco_liberado_mb : 0;
            
            if (pNum && tot > 0) pNum.textContent = `${proc} / ${tot}`;
            else if (pNum) pNum.textContent = "Verificando...";
            if (rEsp) rEsp.textContent = `${lib} MB`;

            const lista = document.getElementById('overlay-categorias');
            if (lista) {
                lista.replaceChildren();
                for (let c of detalhes.categorias) {
                    const div = document.createElement('div');
                    div.className = 'atividade-item';
                    let st = 'Aguardando';
                    let cor = 'var(--cor-texto-secundario)';
                    let iconeBadge = '[~]';

                    if (c.status === 'limpando') {
                        st = c.percentual !== undefined ? `Limpando ${c.percentual}%` : 'Limpando...';
                        cor = 'var(--cor-alerta-texto)';
                        iconeBadge = '[⚡]';
                    } else if (c.status === 'concluido') {
                        st = 'Concluído';
                        cor = 'var(--cor-sucesso-texto)';
                        iconeBadge = '[✓]';
                    } else if (c.status === 'parcial') {
                        st = 'Exceções';
                        cor = 'var(--cor-alerta-texto)';
                        iconeBadge = '[!]';
                    } else if (c.status === 'falhou') {
                        st = 'Falhou';
                        cor = 'var(--cor-erro-texto)';
                        iconeBadge = '[X]';
                    } else if (c.status === 'vazio') {
                        st = 'Nada a limpar';
                        cor = 'var(--cor-texto-secundario)';
                        iconeBadge = '[-]';
                    }

                    div.innerHTML = `
                      <div class="atividade-item-texto">
                        <span style="color:${cor}; font-weight:600; min-width:24px;">${iconeBadge}</span>
                        <span>${c.nome}</span>
                      </div>
                      <span style="color:${cor}; font-size:11px;">${st}</span>
                    `;
                    lista.appendChild(div);
                }
            }
        } else {
            if (detalhesContainer) detalhesContainer.style.display = 'none';
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



        const btnCancelar = document.getElementById('overlay-btn-cancelar');
        if (btnCancelar) btnCancelar.style.display = 'none';
        const detalhesContainer = document.getElementById('overlay-detalhes-limpeza');
        if (detalhesContainer) detalhesContainer.style.display = 'none';
        const categoriasLista = document.getElementById('overlay-categorias');
        if (categoriasLista) categoriasLista.replaceChildren();

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



        if (_hideTimeout) {
            clearTimeout(_hideTimeout);
            _hideTimeout = null;
        }

        _hideTimeout = setTimeout(() => {

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
