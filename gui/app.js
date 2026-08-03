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
    await Phoenix.ui.visualEffects.initialize();
    await Phoenix.pages.inicio.carregarHardwareInicial();
    
    // 3. Router e Handlers finais
    registrarBotoesAcao();

    // 4. Inicia Navegação (avalia Hash inicial ou "inicio")
    Phoenix.router.initialize();
  }

  bootstrap();

})(window.Phoenix);
