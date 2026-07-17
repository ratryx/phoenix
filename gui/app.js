/* ============================================================
   Phoenix Optimizer — GUI Frontend Logic (v2 — rewrite)
   ============================================================
   Toda chamada de funcionalidade real (diagnóstico, limpeza,
   otimização, serviços) vai para pywebview.api.<método>, que
   delega ao mesmo núcleo Python usado pelo modo CLI.

   Estrutura:
   - IIFE para evitar poluição global
   - Apenas awaitJob, mostrarOverlay e esconderOverlay globais
   - Estado centralizado em STATE
   - Todo listener registrado dentro de pywebviewready
   ============================================================ */

(function () {
  "use strict";

  const STATE = Phoenix.state;
  const bridge = Phoenix.bridge;
  const jobs = Phoenix.jobs;
  const lifecycle = Phoenix.lifecycle;
  const router = Phoenix.router;
  const feedback = Phoenix.ui.feedback;

  const mostrarOverlay = feedback.mostrarOverlay;
  const esconderOverlay = feedback.esconderOverlay;
  const atualizarOverlay = feedback.atualizarOverlay;
  const confirmarModal = feedback.confirmarModal;
  const awaitJob = jobs.awaitJob;

  router.setPageLoader(carregarConteudoPagina);


  // ──────────────────────────────────────────────
  //  Estado centralizado
  // ──────────────────────────────────────────────

  
  
  // ──────────────────────────────────────────────
  //  Utilitários puros
  // ──────────────────────────────────────────────

  function corPorPercentual(pct) {
    if (pct >= 90) return "erro";
    if (pct >= 70) return "alerta";
    return "";
  }
  Phoenix.ui = Phoenix.ui || {};
  Phoenix.ui.corPorPercentual = corPorPercentual;

  // ──────────────────────────────────────────────
  //  Overlay (globais — usados pelo backend)
  // ──────────────────────────────────────────────

  
  
  // ──────────────────────────────────────────────
  //  awaitJob — global, com timeout de 60s
  // ──────────────────────────────────────────────

  
  // ──────────────────────────────────────────────
  //  Modal de Confirmação Customizado
  // ──────────────────────────────────────────────

  
  // ──────────────────────────────────────────────
  //  Navegação entre páginas
  // ──────────────────────────────────────────────

  
  function carregarConteudoPagina(pagina) {
    switch (pagina) {
      case "diagnostico":
        Phoenix.pages.diagnostico.load();
        break;
      case "hardware":
        Phoenix.pages.hardware.load();
        break;
      case "limpeza":
        Phoenix.pages.limpeza.load();
        break;
      case "servicos":
        Phoenix.pages.servicos.load();
        break;
      case "historico":
        Phoenix.pages.historico.load();
        break;
      case "hwmonitor":
        Phoenix.pages.hwmonitor.load();
        break;
      case "otimizacao":
        Phoenix.pages.otimizacao.load();
        break;
      // inicio, relatorio — conteúdo estático ou gerado sob demanda
    }
  }

  // ──────────────────────────────────────────────
  //  Qualidade visual adaptativa
  // ──────────────────────────────────────────────

  function aplicarNivelQualidade(nivel) {
    STATE.nivelQualidadeVisual = nivel;
    document.body.classList.remove(
      "qualidade-alta",
      "qualidade-media",
      "qualidade-baixa"
    );

    if (nivel === "alto") {
      document.body.classList.add("qualidade-alta");
      gerarParticulas();
    } else if (nivel === "medio") {
      document.body.classList.add("qualidade-media");
    } else {
      document.body.classList.add("qualidade-baixa");
    }
  }

  function gerarParticulas() {
    var camada = document.getElementById("camada-particulas");
    if (!camada) return;
    camada.innerHTML = "";

    var quantidade = 14;
    for (var i = 0; i < quantidade; i++) {
      var p = document.createElement("div");
      p.className = "particula";
      var tamanho = 4 + Math.random() * 10;
      p.style.width = tamanho + "px";
      p.style.height = tamanho + "px";
      p.style.left = Math.random() * 100 + "%";
      p.style.top = 60 + Math.random() * 40 + "%";
      p.style.animationDuration = 8 + Math.random() * 10 + "s";
      p.style.animationDelay = Math.random() * 10 + "s";
      camada.appendChild(p);
    }
  }

  async function aplicarQualidadeVisual() {
    try {
      var nivel = await bridge.call("obter_nivel_qualidade_visual");
      aplicarNivelQualidade(nivel || "medio");
    } catch (e) {
      aplicarNivelQualidade("medio");
    }
  }

  

  

  // ──────────────────────────────────────────────
  //  Diagnóstico completo
  // ──────────────────────────────────────────────



  // ──────────────────────────────────────────────
  //  HWMonitor — monitoramento em tempo real
  // ──────────────────────────────────────────────



  // ──────────────────────────────────────────────
  //  Hardware detalhado
  // ──────────────────────────────────────────────



  // ──────────────────────────────────────────────
  //  Ponto de restauração (extraído para operations)
  // ──────────────────────────────────────────────



  // ──────────────────────────────────────────────
  //  Otimização (extraída para gui/js/pages/otimizacao.js)
  // ──────────────────────────────────────────────

  // ──────────────────────────────────────────────
  //  Rotina completa + Relatório
  // ──────────────────────────────────────────────

  function executarRotinaCompleta() {
    Phoenix.operations.restorePoint.runProtected(async function () {
      mostrarOverlay(
        "Executando rotina completa — isso pode levar alguns minutos...", true
      );
      try {
        var jobRes = await bridge.call("executar_rotina_completa", "");
        if (!jobRes || !jobRes.job_id) { esconderOverlay(true); return; }
        var resultado = await awaitJob(jobRes.job_id);
        esconderOverlay(true);

        if (!resultado || !resultado.ok) {
          await confirmarModal(
            'Erro na Rotina',
            "Erro ao executar rotina completa: " + (resultado && resultado.erro || "Erro desconhecido"),
            '🚨'
          );
          return;
        }

        router.navigate("relatorio");
        Phoenix.pages.relatorio.showResult(resultado);
      } catch (e) {
        console.error("[ERRO] Rotina completa:", e);
        esconderOverlay(true);
      }
    });
  }

  // ──────────────────────────────────────────────
  //  Registro de event listeners da sidebar
  // ──────────────────────────────────────────────

  function registrarSidebar() {
    document
      .querySelectorAll(".item-menu[data-pagina]")
      .forEach(function (item) {
        item.addEventListener("click", function () {
          var pagina = item.dataset.pagina;
          router.navigate(pagina);
          carregarConteudoPagina(pagina);
        });
      });
  }

  // ──────────────────────────────────────────────
  //  Registro dos botões de ação
  // ──────────────────────────────────────────────

  function registrarBotoesAcao() {
    // Diagnóstico
    var btnDiag = document.getElementById("btn-atualizar-diagnostico");
    if (btnDiag) btnDiag.addEventListener("click", () => Phoenix.pages.diagnostico.load());

    // Rotina completa — sidebar e card
    var btnRotina = document.getElementById("btn-rotina-completa");
    if (btnRotina) btnRotina.addEventListener("click", executarRotinaCompleta);

    var btnRotinaCard = document.getElementById("btn-rotina-completa-card");
    if (btnRotinaCard)
      btnRotinaCard.addEventListener("click", executarRotinaCompleta);

  }

  // ──────────────────────────────────────────────
  //  Controles da janela (minimizar / fechar)
  // ──────────────────────────────────────────────

  function registrarBotoesJanela() {
    var btnMin = document.getElementById("btn-minimizar");
    if (btnMin) {
      btnMin.addEventListener("click", function () {
        bridge.call("minimizar_janela");
      });
    }

    var btnFechar = document.getElementById("btn-fechar");
    if (btnFechar) {
      btnFechar.addEventListener("click", function () {
        bridge.call("fechar_janela");
      });
    }
  }

  // ──────────────────────────────────────────────
  //  Drag da janela (throttled com rAF)
  // ──────────────────────────────────────────────

  function registrarDrag() {
    var estaArrastando = false;
    var ultimoX = 0;
    var ultimoY = 0;
    var animFrameId = null;

    function processarMovimento() {
      if (estaArrastando && bridge.isReady()) {
        bridge.call("mover_janela", ultimoX, ultimoY);
        animFrameId = requestAnimationFrame(processarMovimento);
      } else {
        animFrameId = null;
      }
    }

    // Elementos que iniciam drag
    var elementosDrag = [];

    var titlebar = document.querySelector(".barra-titulo");
    if (titlebar) elementosDrag.push(titlebar);

    document.querySelectorAll(".cabecalho-pagina").forEach(function (el) {
      elementosDrag.push(el);
    });

    elementosDrag.forEach(function (el) {
      el.addEventListener("mousedown", function (e) {
        // Ignorar cliques em elementos interativos
        if (
          e.target.closest("button") ||
          e.target.closest("input") ||
          e.target.closest("a") ||
          e.target.closest(".controles-janela")
        ) {
          return;
        }

        estaArrastando = true;
        ultimoX = e.screenX;
        ultimoY = e.screenY;

        var winX = e.screenX - e.clientX;
        var winY = e.screenY - e.clientY;

        if (bridge.isReady()) {
          bridge.call("iniciar_drag", e.screenX, e.screenY, winX, winY);
        }

        if (!animFrameId) {
          animFrameId = requestAnimationFrame(processarMovimento);
        }
      });
    });

    // mousemove — só atualiza coordenadas, sem flood de chamadas API
    window.addEventListener("mousemove", function (e) {
      if (estaArrastando) {
        ultimoX = e.screenX;
        ultimoY = e.screenY;
      }
    });

    // mouseup — para o drag
    window.addEventListener("mouseup", function () {
      if (estaArrastando) {
        estaArrastando = false;
        if (animFrameId) {
          cancelAnimationFrame(animFrameId);
          animFrameId = null;
        }
        if (bridge.isReady()) {
          bridge.call("parar_drag");
        }
      }
    });
  }

  // ──────────────────────────────────────────────
  //  Lógica de Seleção de Cliente (Portable)
  // ──────────────────────────────────────────────

  async function exibirSelecaoCliente() {
    const tela = document.getElementById('tela-selecao-cliente');
    if (tela) tela.style.display = 'flex';
    
    const res = await bridge.call("obter_clientes_portable");
    const lista = document.getElementById('lista-clientes-portable');
    
    if (res.clientes && res.clientes.length > 0) {
      lista.innerHTML = `
        <div style="font-size:13px;color:var(--cor-texto-secundario);
          margin-bottom:10px">Clientes anteriores:</div>
        ${res.clientes.map(c => `
          <div class="card" style="cursor:pointer;margin-bottom:8px;
            display:flex;align-items:center;gap:16px;
            transition:border-color 0.15s"
            onmouseover="this.style.borderColor='var(--cor-primaria)'"
            onmouseout="this.style.borderColor=''"
            onclick="selecionarCliente('${c.nome.replace(/'/g, "\\'")}')">
            <div style="font-size:28px">👤</div>
            <div style="flex:1">
              <div style="font-weight:600">${c.nome}</div>
              <div class="texto-secundario">
                ${c.total_atendimentos} atendimento(s) · 
                Último: ${c.ultimo_atendimento || 'Nunca'}
              </div>
            </div>
            <button style="background:transparent;border:none;color:var(--cor-texto-secundario);
              cursor:pointer;font-size:16px;padding:8px" 
              title="Remover perfil"
              onmouseover="this.style.color='var(--cor-erro)'"
              onmouseout="this.style.color='var(--cor-texto-secundario)'"
              onclick="event.stopPropagation(); removerCliente('${c.id.replace(/'/g, "\\'")}', '${c.nome.replace(/'/g, "\\'")}')">
              🗑️
            </button>
            <div style="color:var(--cor-primaria)">→</div>
          </div>
        `).join('')}
      `;
    } else {
      lista.innerHTML = '';
    }
  }

  async function selecionarCliente(nome) {
    const res = await bridge.call("selecionar_cliente", nome);
    if (res.ok) {
      const tela = document.getElementById('tela-selecao-cliente');
      if (tela) tela.style.display = 'none';
      
      // Atualizar header com nome do cliente
      const versaoEl = document.querySelector('.sidebar .versao');
      if (versaoEl) versaoEl.textContent = `v2.0 · ${nome}`;
    }
  }

  window.removerCliente = async function(id, nome) {
    const confirm = await confirmarModal(
      "Remover Cliente",
      `Deseja realmente apagar o histórico de "${nome}"?`,
      "🗑️"
    );
    if (!confirm) return;
    
    const res = await bridge.call("remover_cliente_portable", id);
    if (res.ok) {
      await exibirSelecaoCliente();
    }
  };

  // Expor pro HTML
  window.selecionarCliente = selecionarCliente;
  window.confirmarNovoCliente = async function() {
    const input = document.getElementById('input-novo-cliente');
    const nome = input?.value?.trim();
    if (!nome) {
      input.style.borderColor = 'var(--cor-erro)';
      setTimeout(() => input.style.borderColor = '', 1500);
      return;
    }
    await selecionarCliente(nome);
  };

  // ──────────────────────────────────────────────
  //  INICIALIZAÇÃO — única entrada
  // ──────────────────────────────────────────────

  
  let bootstrapStarted = false;

  async function bootstrap() {
    if (bootstrapStarted) return;
    bootstrapStarted = true;

    await bridge.whenReady();

    // Verificar modo portable
    try {
      const modoRes = await bridge.call("obter_modo_portable");
      if (modoRes.portable) {
        await exibirSelecaoCliente();
      }
    } catch(e) {}

    await aplicarQualidadeVisual();
    await Phoenix.pages.inicio.carregarHardwareInicial();
    registrarSidebar();
    registrarBotoesAcao();
    registrarBotoesJanela();
    registrarDrag();
    Phoenix.pages.inicio.iniciarAtualizacaoTempoReal();
  }

  bootstrap();
})();
