/* ============================================================
   Phoenix Optimizer — Composition Root & Bootstrap (v2)
   ============================================================ */

(function (Phoenix) {
  "use strict";

  const STATE = Phoenix.state;
  const bridge = Phoenix.bridge;
  const router = Phoenix.router;

  // ──────────────────────────────────────────────
  //  Page Loader Map
  // ──────────────────────────────────────────────

  const pageLoaders = {
    inicio: Phoenix.pages.inicio.load,
    diagnostico: Phoenix.pages.diagnostico.load,
    hardware: Phoenix.pages.hardware.load,
    hwmonitor: Phoenix.pages.hwmonitor.load,
    limpeza: Phoenix.pages.limpeza.load,
    otimizacao: Phoenix.pages.otimizacao.load,
    servicos: Phoenix.pages.servicos.load,
    historico: Phoenix.pages.historico.load,
    relatorio: Phoenix.pages.relatorio.load
  };

  function carregarConteudoPagina(pagina) {
    const loader = pageLoaders[pagina];
    if (loader) loader();
  }

  router.setPageLoader(carregarConteudoPagina);

  // ──────────────────────────────────────────────
  //  Compatibilidade Global e Visual
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
  //  Registro de Botões Essenciais (App)
  // ──────────────────────────────────────────────

  function registrarBotoesAcao() {
    // Diagnóstico
    var btnDiag = document.getElementById("btn-atualizar-diagnostico");
    if (btnDiag) btnDiag.addEventListener("click", () => Phoenix.pages.diagnostico.load());

    // Rotina completa — sidebar e card
    var btnRotina = document.getElementById("btn-rotina-completa");
    if (btnRotina) btnRotina.addEventListener("click", Phoenix.operations.routine.execute);

    var btnRotinaCard = document.getElementById("btn-rotina-completa-card");
    if (btnRotinaCard)
      btnRotinaCard.addEventListener("click", Phoenix.operations.routine.execute);
  }

  // ──────────────────────────────────────────────
  //  INICIALIZAÇÃO — Composition Root
  // ──────────────────────────────────────────────

  let bootstrapStarted = false;

  async function bootstrap() {
    if (bootstrapStarted) return;
    bootstrapStarted = true;

    await bridge.whenReady();

    // 1. Recursos Principais de UI e Sessão
    Phoenix.ui.windowControls.initialize();
    await Phoenix.features.clientSession.initialize();
    
    // 2. Recursos de Hardware e Visual
    await aplicarQualidadeVisual();
    await Phoenix.pages.inicio.carregarHardwareInicial();
    
    // 3. Router e Handlers finais
    registrarBotoesAcao();
    Phoenix.pages.inicio.iniciarAtualizacaoTempoReal();

    // 4. Inicia Navegação (avalia Hash inicial ou "inicio")
    Phoenix.router.initialize();
  }

  bootstrap();

})(window.Phoenix);
