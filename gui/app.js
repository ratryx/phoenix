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

  function formatarBytes(mb) {
    if (mb >= 1024) return (mb / 1024).toFixed(2) + " GB";
    return mb.toFixed(1) + " MB";
  }

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
        // Conteúdo carrega ao clicar no botão dedicado
        break;
      case "servicos":
        carregarServicos();
        break;
      case "historico":
        carregarHistorico();
        break;
      case "hwmonitor":
        carregarSensores();
        break;
      // inicio, otimizacao, relatorio — conteúdo estático ou gerado sob demanda
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

  function carregarSensores() {
    var container = document.getElementById('pagina-hwmonitor');
    if (!container) return;
    var hw = STATE.hardware;
    if (!hw) return;

    var gpus = hw.gpus || [];
    var gpuNome = gpus.length > 0 ? gpus[0].nome : 'GPU';
    
    container.innerHTML =
      '<div class="cabecalho-pagina">' +
      '<div>' +
      '<h1>Monitor de Sensores</h1>' +
      '<p>Monitoramento em tempo real — atualiza a cada 3s</p>' +
      '</div>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">' +
      
      '<!-- CPU -->' +
      '<div class="card">' +
      '<div style="color:var(--cor-primaria);font-weight:600;margin-bottom:12px">CPU</div>' +
      '<div style="font-size:36px;font-weight:700" id="hw-cpu-total">--<span style="font-size:16px">%</span></div>' +
      '<div class="barra-progresso" style="margin:8px 0">' +
      '<div class="preenchimento" id="hw-cpu-bar" style="width:0%;transition:width 0.5s"></div>' +
      '</div>' +
      '<div class="texto-secundario" id="hw-cpu-freq">-- MHz</div>' +
      '<div style="margin-top:16px">' +
      '<div style="font-size:11px;color:var(--cor-texto-terciario);text-transform:uppercase;margin-bottom:8px">Por núcleo</div>' +
      '<div id="hw-nucleos" style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px"></div>' +
      '</div>' +
      '</div>' +

      '<!-- GPU -->' +
      '<div class="card">' +
      '<div style="color:var(--cor-primaria);font-weight:600;margin-bottom:12px" id="hw-gpu-nome">' + gpuNome + '</div>' +
      '<div style="font-size:36px;font-weight:700" id="hw-gpu-uso">--<span style="font-size:16px">%</span></div>' +
      '<div class="barra-progresso" style="margin:8px 0">' +
      '<div class="preenchimento" id="hw-gpu-bar" style="width:0%;transition:width 0.5s"></div>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px">' +
      '<div class="card-metrica" style="padding:12px">' +
      '<div class="rotulo">Temperatura</div>' +
      '<div class="valor" id="hw-gpu-temp" style="font-size:20px">--°C</div>' +
      '</div>' +
      '<div class="card-metrica" style="padding:12px">' +
      '<div class="rotulo">VRAM</div>' +
      '<div class="valor" id="hw-gpu-vram" style="font-size:16px">-- / -- MB</div>' +
      '</div>' +
      '</div>' +
      '</div>' +

      '<!-- RAM -->' +
      '<div class="card">' +
      '<div style="color:var(--cor-primaria);font-weight:600;margin-bottom:12px">Memória RAM</div>' +
      '<div style="font-size:36px;font-weight:700" id="hw-ram-pct">--<span style="font-size:16px">%</span></div>' +
      '<div class="barra-progresso" style="margin:8px 0">' +
      '<div class="preenchimento" id="hw-ram-bar" style="width:0%;transition:width 0.5s"></div>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px">' +
      '<div class="card-metrica" style="padding:12px">' +
      '<div class="rotulo">Em uso</div>' +
      '<div class="valor" id="hw-ram-usada" style="font-size:18px">-- GB</div>' +
      '</div>' +
      '<div class="card-metrica" style="padding:12px">' +
      '<div class="rotulo">Disponível</div>' +
      '<div class="valor" id="hw-ram-livre" style="font-size:18px">-- GB</div>' +
      '</div>' +
      '</div>' +
      '</div>' +

      '<!-- Disco I/O -->' +
      '<div class="card">' +
      '<div style="color:var(--cor-primaria);font-weight:600;margin-bottom:12px">Disco — Atividade em tempo real</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:8px">' +
      '<div>' +
      '<div class="texto-secundario">Leitura</div>' +
      '<div style="font-size:28px;font-weight:700;color:var(--cor-info)" id="hw-disk-read">--<span style="font-size:13px"> MB/s</span></div>' +
      '</div>' +
      '<div>' +
      '<div class="texto-secundario">Escrita</div>' +
      '<div style="font-size:28px;font-weight:700;color:var(--cor-alerta)" id="hw-disk-write">--<span style="font-size:13px"> MB/s</span></div>' +
      '</div>' +
      '</div>' +
      '</div>' +

      '</div>';

    // Inicia polling específico pro HWMonitor
    /* if (_sensoresInterval) */ lifecycle.clearInterval("sensores");
    lifecycle.setInterval("sensores", async function() {
      try {
        var res = await bridge.call("obter_metricas_completas");
        if (!res || !res.ok) return;

        // Atualiza CPU
        var cpuVal = document.getElementById('hw-cpu-total');
        var cpuBar = document.getElementById('hw-cpu-bar');
        var cpuFreq = document.getElementById('hw-cpu-freq');
        
        if (cpuVal) cpuVal.innerHTML = res.cpu.total + '<span style="font-size:16px">%</span>';
        if (cpuBar) {
          cpuBar.style.width = res.cpu.total + '%';
          cpuBar.className = 'preenchimento ' + corPorPercentual(res.cpu.total);
        }
        if (cpuFreq) cpuFreq.textContent = res.cpu.freq_mhz ? res.cpu.freq_mhz + ' MHz' : '-- MHz';
        
        var nucleosEl = document.getElementById('hw-nucleos');
        if (nucleosEl && res.cpu.por_nucleo) {
          nucleosEl.innerHTML = res.cpu.por_nucleo.map(function(pct, i) {
            var cor = pct > 90 ? 'var(--cor-erro)' : pct > 70 ? 'var(--cor-alerta)' : 'var(--cor-texto)';
            return '<div style="text-align:center">' +
              '<div style="font-size:10px;color:var(--cor-texto-terciario)">C' + (i+1) + '</div>' +
              '<div style="font-size:13px;font-weight:600;color:' + cor + '">' + pct + '%</div>' +
              '</div>';
          }).join('');
        }

        // Atualiza RAM
        var ramPct = document.getElementById('hw-ram-pct');
        var ramBar = document.getElementById('hw-ram-bar');
        var ramUsada = document.getElementById('hw-ram-usada');
        var ramLivre = document.getElementById('hw-ram-livre');

        if (ramPct) ramPct.innerHTML = res.ram.percent + '<span style="font-size:16px">%</span>';
        if (ramBar) {
          ramBar.style.width = res.ram.percent + '%';
          ramBar.className = 'preenchimento ' + corPorPercentual(res.ram.percent);
        }
        if (ramUsada) ramUsada.textContent = res.ram.usada_gb + ' GB';
        if (ramLivre) ramLivre.textContent = res.ram.disponivel_gb + ' GB';

        // Atualiza GPU
        var gpuUso = document.getElementById('hw-gpu-uso');
        var gpuBar = document.getElementById('hw-gpu-bar');
        var gpuTemp = document.getElementById('hw-gpu-temp');
        var gpuVram = document.getElementById('hw-gpu-vram');

        if (res.gpu) {
          var g = res.gpu;
          if (gpuUso) gpuUso.innerHTML = g.uso + '<span style="font-size:16px">%</span>';
          if (gpuBar) {
            gpuBar.style.width = g.uso + '%';
            gpuBar.className = 'preenchimento ' + corPorPercentual(g.uso);
          }
          if (gpuTemp) {
            var corTemp = g.temp >= 85 ? 'var(--cor-erro)' : g.temp >= 70 ? 'var(--cor-alerta)' : 'var(--cor-sucesso)';
            gpuTemp.innerHTML = '<span style="color:' + corTemp + '">' + g.temp + '°C</span>';
          }
          if (gpuVram) gpuVram.textContent = g.vram_usada + ' / ' + g.vram_total + ' MB';
        }

        // Atualiza Disco I/O
        var diskRead = document.getElementById('hw-disk-read');
        var diskWrite = document.getElementById('hw-disk-write');
        
        if (diskRead) diskRead.innerHTML = res.disco.leitura_mb + '<span style="font-size:13px"> MB/s</span>';
        if (diskWrite) diskWrite.innerHTML = res.disco.escrita_mb + '<span style="font-size:13px"> MB/s</span>';

      } catch(e) {}
    }, 3000);
  }

  // ──────────────────────────────────────────────
  //  Hardware detalhado
  // ──────────────────────────────────────────────



  // ──────────────────────────────────────────────
  //  Limpeza
  // ──────────────────────────────────────────────

  async function executarLimpeza() {
    mostrarOverlay("Limpando arquivos temporários...", true);
    try {
      var jobRes = await bridge.call("executar_limpeza");
      if (!jobRes || !jobRes.job_id) {
        esconderOverlay(true);
        return;
      }
      var resultado = await awaitJob(jobRes.job_id);
      esconderOverlay(true);
      renderizarLimpeza(resultado);
    } catch (e) {
      console.error("[ERRO] Limpeza:", e);
      esconderOverlay(true);
    }
  }

  function renderizarLimpeza(resultado) {
    var container = document.getElementById("conteudo-limpeza");
    if (!container) return;

    if (!resultado || !resultado.ok) {
      container.innerHTML =
        '<div class="card"><span class="badge erro">Erro</span> ' +
        ((resultado && resultado.erro) || "Erro desconhecido") +
        "</div>";
      return;
    }

    container.innerHTML =
      '<div class="card">' +
      '<span class="badge sucesso">Concluído</span>' +
      '<p style="margin-top:10px">Espaço total liberado: <strong>' +
      formatarBytes(resultado.espaco_liberado_mb) +
      "</strong></p>" +
      "</div>";
  }

  // ──────────────────────────────────────────────
  //  Modal de confirmação do ponto de restauração
  // ──────────────────────────────────────────────

  function exibirModalRestauracao(titulo, mensagem, tipo, aoConfirmar, aoCancelar) {
    var modal = document.getElementById("modal-restauracao");
    var tituloEl = document.getElementById("modal-titulo");
    var mensagemEl = document.getElementById("modal-mensagem");
    var iconEl = document.getElementById("modal-icon");
    var btnConfirmar = document.getElementById("btn-modal-confirmar");
    var btnCancelar = document.getElementById("btn-modal-cancelar");

    if (!modal) return;

    tituloEl.textContent = titulo;
    mensagemEl.textContent = mensagem;

    // Reset classes e ícone
    iconEl.className = "modal-status-icon " + tipo;
    if (tipo === "sucesso") {
      iconEl.textContent = "✓";
    } else if (tipo === "erro" || tipo === "alerta") {
      iconEl.textContent = "⚠";
    }

    // Ajustar textos dos botões
    if (tipo === "sucesso") {
      btnConfirmar.textContent = "Confirmar e Prosseguir";
      btnConfirmar.className = "botao primario";
    } else {
      btnConfirmar.textContent = "Continuar mesmo assim";
      btnConfirmar.className = "botao primario";
    }
    btnCancelar.textContent = "Cancelar";

    // Garantir botão confirmar visível (pode ter sido escondido antes)
    btnConfirmar.style.display = "";

    // Event handlers (com remoção automática)
    function cliqueConfirmar() {
      modal.classList.remove("visivel");
      desregistrar();
      aoConfirmar();
    }

    function cliqueCancelar() {
      modal.classList.remove("visivel");
      desregistrar();
      aoCancelar();
    }

    function desregistrar() {
      btnConfirmar.removeEventListener("click", cliqueConfirmar);
      btnCancelar.removeEventListener("click", cliqueCancelar);
    }

    btnConfirmar.addEventListener("click", cliqueConfirmar);
    btnCancelar.addEventListener("click", cliqueCancelar);

    modal.classList.add("visivel");
  }

  // ──────────────────────────────────────────────
  //  Ponto de restauração (antes de otimizações)
  // ──────────────────────────────────────────────

  async function comPontoRestauracao(acaoFn) {
    if (STATE.restorePointCreatedThisSession) {
      await acaoFn();
      return;
    }

    mostrarOverlay('Criando ponto de restauração...', true);
    
    // Simular progresso enquanto o PowerShell roda
    atualizarOverlay('Invocando PowerShell...', 10);
    
    const progressoTimer = setInterval(() => {
      const fill = document.getElementById('overlay-barra-fill');
      if (fill && !fill.classList.contains('indeterminado')) {
        const atual = parseFloat(fill.style.width) || 10;
        if (atual < 85) {
          atualizarOverlay('Criando ponto de restauração do sistema...', atual + 5);
        }
      }
    }, 2000);
    
    try {
      const jobRes = await bridge.call("criar_ponto_restauracao");
      const res = await window.awaitJob(jobRes.job_id);
      clearInterval(progressoTimer);
      
      if (res && res.ok) {
        STATE.restorePointCreatedThisSession = true;
        atualizarOverlay('Ponto de restauração criado!', 100);
        setTimeout(async () => {
          esconderOverlay(true, true);
          await acaoFn();
        }, 800);
      } else {
        esconderOverlay(true, false);
        setTimeout(async () => {
          const continuar = await confirmarModal(
            'Ponto de restauração indisponível',
            'Não foi possível criar um ponto de restauração do sistema. Deseja continuar com a otimização mesmo assim? Em caso de problemas, não será possível reverter automaticamente.',
            '⚠️'
          );
          if (continuar) {
            STATE.restorePointCreatedThisSession = true; // Para não perguntar novamente
            await acaoFn();
          }
        }, 1300); // 1300ms porque o esconderOverlay destrutivo demora 1200ms para sumir da tela
      }
    } catch(e) {
      console.error("[ERRO] Ponto de restauração:", e);
      clearInterval(progressoTimer);
      esconderOverlay(true, false);
      setTimeout(async () => {
        const continuar = await confirmarModal(
          'Erro ao criar ponto de restauração',
          'Ocorreu um erro interno ao tentar criar o ponto de restauração. Deseja continuar com a otimização mesmo assim?',
          '🚨'
        );
        if (continuar) {
          STATE.restorePointCreatedThisSession = true;
          await acaoFn();
        }
      }, 1300);
    }
  }

  // ──────────────────────────────────────────────
  //  Otimização
  // ──────────────────────────────────────────────

  function exibirResultadoOtimizacao(resultado, mensagemSucesso) {
    var container = document.getElementById("resultado-otimizacao");
    if (!container) return;

    if (!resultado || !resultado.ok) {
      container.innerHTML =
        '<div class="card"><span class="badge erro">Erro</span> ' +
        ((resultado && resultado.erro) || "Erro desconhecido") +
        "</div>";
      return;
    }
    container.innerHTML =
      '<div class="card"><span class="badge sucesso">Concluído</span> ' +
      mensagemSucesso +
      "</div>";
  }

  async function executarOtimizacaoGeral() {
    comPontoRestauracao(async function () {
      mostrarOverlay("Aplicando otimização geral...", true);
      try {
        var jobRes = await bridge.call("executar_otimizacao_geral");
        if (!jobRes || !jobRes.job_id) { esconderOverlay(true); return; }
        var resultado = await awaitJob(jobRes.job_id);
        esconderOverlay(true);
        exibirResultadoOtimizacao(resultado, "Otimização geral aplicada.");
      } catch (e) {
        console.error("[ERRO] Otimização geral:", e);
        esconderOverlay(true);
      }
    });
  }

  async function executarOtimizacaoGaming() {
    comPontoRestauracao(async function () {
      mostrarOverlay("Aplicando otimização para jogos...", true);
      try {
        var jobRes = await bridge.call("executar_otimizacao_gaming", false);
        if (!jobRes || !jobRes.job_id) { esconderOverlay(true); return; }
        var resultado = await awaitJob(jobRes.job_id);
        esconderOverlay(true);
        exibirResultadoOtimizacao(
          resultado,
          "Otimização para jogos aplicada. Reinicie o PC para garantir efeito completo."
        );
      } catch (e) {
        console.error("[ERRO] Otimização gaming:", e);
        esconderOverlay(true);
      }
    });
  }

  async function executarOtimizacaoDisco() {
    mostrarOverlay("Otimizando disco — isso pode levar alguns minutos...", true);
    try {
      var jobRes = await bridge.call("otimizar_disco");
      if (!jobRes || !jobRes.job_id) { esconderOverlay(true); return; }
      var resultado = await awaitJob(jobRes.job_id);
      esconderOverlay(true);
      exibirResultadoOtimizacao(resultado, "Otimização de disco concluída.");
    } catch (e) {
      console.error("[ERRO] Otimização disco:", e);
      esconderOverlay(true);
    }
  }

  // ──────────────────────────────────────────────
  //  Serviços
  // ──────────────────────────────────────────────

  async function carregarServicos() {
    var container = document.getElementById("conteudo-servicos");
    if (!container) return;

    container.innerHTML =
      '<p class="texto-secundario">Carregando serviços...</p>';
    mostrarOverlay("Consultando serviços do Windows...");

    try {
      var jobRes = await bridge.call("listar_servicos");
      if (!jobRes || !jobRes.job_id) { esconderOverlay(); return; }
      var resultado = await awaitJob(jobRes.job_id);
      esconderOverlay();

      if (!resultado || !resultado.ok) {
        container.innerHTML =
          '<div class="card"><span class="badge erro">Erro</span> ' +
          ((resultado && resultado.erro) || "Erro desconhecido") +
          "</div>";
        return;
      }

      var linhas = (resultado.servicos || [])
        .map(function (s) {
          var ativo = s.status === "Rodando";
          return (
            "<tr>" +
            "<td>" +
            "<strong>" + s.nome_amigavel + "</strong>" +
            '<div class="texto-terciario">' + s.descricao + "</div>" +
            "</td>" +
            "<td>" +
            '<span class="badge ' + (ativo ? "sucesso" : "neutro") + '">' +
            s.status +
            "</span>" +
            "</td>" +
            "<td>" +
            '<div class="toggle ' + (ativo ? "ativo" : "") + '"' +
            ' data-servico="' + s.nome_servico + '"' +
            ' data-ativo="' + ativo + '">' +
            '<div class="bola"></div>' +
            "</div>" +
            "</td>" +
            "</tr>"
          );
        })
        .join("");

      container.innerHTML =
        '<div class="card">' +
        '<table class="tabela-dados">' +
        "<thead><tr><th>Serviço</th><th>Status</th><th>Ação</th></tr></thead>" +
        "<tbody>" + linhas + "</tbody>" +
        "</table>" +
        "</div>";

      // Registrar toggles dos serviços
      container.querySelectorAll(".toggle").forEach(function (toggle) {
        toggle.addEventListener("click", function () {
          var nomeServico = toggle.dataset.servico;
          var estaAtivo = toggle.dataset.ativo === "true";

          comPontoRestauracao(async function () {
            mostrarOverlay(
              estaAtivo ? "Desativando serviço..." : "Ativando serviço..."
            );
            try {
              var metodoAcao = estaAtivo
                ? "desativar_servico"
                : "ativar_servico";
              var jobRes = await bridge.call(metodoAcao, nomeServico);
              if (!jobRes || !jobRes.job_id) { esconderOverlay(); return; }
              var resultado = await awaitJob(jobRes.job_id);
              esconderOverlay();

              if (resultado && resultado.ok) {
                toggle.classList.toggle("ativo");
                toggle.dataset.ativo = (!estaAtivo).toString();
              }
            } catch (e) {
              console.error("[ERRO] Toggle serviço:", e);
              esconderOverlay();
            }
          });
        });
      });
    } catch (err) {
      console.error("[ERRO] Serviços:", err);
      esconderOverlay();
      container.innerHTML = '<p class="texto-secundario">Erro ao carregar serviços.</p>';
    }
  }

  // ──────────────────────────────────────────────
  //  Histórico
  // ──────────────────────────────────────────────

  async function carregarHistorico() {
    var container = document.getElementById("conteudo-historico");
    if (!container) return;

    container.innerHTML =
      '<p class="texto-secundario">Carregando histórico...</p>';
    mostrarOverlay("Consultando histórico...");

    try {
      var jobRes = await bridge.call("obter_historico");
      if (!jobRes || !jobRes.job_id) { esconderOverlay(); return; }
      var resultado = await awaitJob(jobRes.job_id);
      esconderOverlay();

      if (!resultado || !resultado.ok) {
        container.innerHTML =
          '<div class="card"><span class="badge erro">Erro</span> ' +
          ((resultado && resultado.erro) || "Erro desconhecido") +
          "</div>";
        return;
      }

      if (!resultado.atendimentos || resultado.atendimentos.length === 0) {
        container.innerHTML =
          '<p class="texto-secundario">Nenhum atendimento registrado ainda.</p>';
        return;
      }

      var linhas = resultado.atendimentos
        .map(function (a) {
          return (
            "<tr>" +
            "<td>" + a.id_atendimento + "</td>" +
            "<td>" + a.cliente + "</td>" +
            "<td>" + a.data_hora + "</td>" +
            "</tr>"
          );
        })
        .join("");

      container.innerHTML =
        '<div class="card">' +
        '<table class="tabela-dados">' +
        "<thead><tr><th>ID</th><th>Cliente</th><th>Data/Hora</th></tr></thead>" +
        "<tbody>" + linhas + "</tbody>" +
        "</table>" +
        "</div>";
    } catch (err) {
      console.error("[ERRO] Histórico:", err);
      esconderOverlay();
    }
  }

  // ──────────────────────────────────────────────
  //  Rotina completa + Relatório
  // ──────────────────────────────────────────────

  function executarRotinaCompleta() {
    comPontoRestauracao(async function () {
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
        renderizarRelatorio(resultado);
      } catch (e) {
        console.error("[ERRO] Rotina completa:", e);
        esconderOverlay(true);
      }
    });
  }

  function renderizarRelatorio(resultado) {
    var container = document.getElementById("conteudo-relatorio");
    if (!container) return;

    var antes = resultado.antes;
    var depois = resultado.depois;

    function linhaComparativa(rotulo, valorAntes, valorDepois, sufixo, menorEMelhor) {
      var diferenca = valorDepois - valorAntes;
      var melhorou = menorEMelhor ? diferenca < 0 : diferenca > 0;
      var corDif =
        Math.abs(diferenca) < 0.01
          ? "neutro"
          : melhorou
            ? "sucesso"
            : "erro";
      var seta =
        Math.abs(diferenca) < 0.01
          ? "="
          : melhorou
            ? "\u25BC"
            : "\u25B2";
      return (
        "<tr>" +
        "<td>" + rotulo + "</td>" +
        "<td>" + valorAntes + sufixo + "</td>" +
        "<td>" + valorDepois + sufixo + "</td>" +
        '<td><span class="badge ' + corDif + '">' +
        seta + " " + Math.abs(diferenca).toFixed(1) + sufixo +
        "</span></td>" +
        "</tr>"
      );
    }

    container.innerHTML =
      '<div class="grade-cards">' +
      '<div class="card-metrica">' +
      '<div class="rotulo">Espaço liberado</div>' +
      '<div class="valor">' + formatarBytes(resultado.espaco_liberado_mb) + "</div>" +
      "</div>" +
      "</div>" +
      '<div class="card">' +
      "<strong>CPU & memória — antes vs depois</strong>" +
      '<table class="tabela-dados" style="margin-top:12px">' +
      "<thead><tr><th>Métrica</th><th>Antes</th><th>Depois</th><th>Variação</th></tr></thead>" +
      "<tbody>" +
      linhaComparativa(
        "Uso de CPU",
        antes.cpu.uso_percentual,
        depois.cpu.uso_percentual,
        "%",
        true
      ) +
      linhaComparativa(
        "Uso de RAM",
        antes.memoria.percentual_uso,
        depois.memoria.percentual_uso,
        "%",
        true
      ) +
      linhaComparativa(
        "RAM disponível",
        antes.memoria.disponivel_gb,
        depois.memoria.disponivel_gb,
        " GB",
        false
      ) +
      "</tbody>" +
      "</table>" +
      "</div>" +
      '<div class="card">' +
      '<span class="badge sucesso">Relatório exportado</span>' +
      '<p class="texto-secundario" style="margin-top:8px">' +
      resultado.relatorio_txt +
      "</p>" +
      "</div>";
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

    // Limpeza
    var btnLimpeza = document.getElementById("btn-executar-limpeza");
    if (btnLimpeza) btnLimpeza.addEventListener("click", executarLimpeza);

    // Otimização geral
    var btnOtGeral = document.getElementById("btn-otimizacao-geral");
    if (btnOtGeral) btnOtGeral.addEventListener("click", executarOtimizacaoGeral);

    // Otimização gaming
    var btnOtGaming = document.getElementById("btn-otimizacao-gaming");
    if (btnOtGaming)
      btnOtGaming.addEventListener("click", executarOtimizacaoGaming);

    // Otimizar disco
    var btnDisco = document.getElementById("btn-otimizar-disco");
    if (btnDisco) btnDisco.addEventListener("click", executarOtimizacaoDisco);

    // Rotina completa — sidebar e card
    var btnRotina = document.getElementById("btn-rotina-completa");
    if (btnRotina) btnRotina.addEventListener("click", executarRotinaCompleta);

    var btnRotinaCard = document.getElementById("btn-rotina-completa-card");
    if (btnRotinaCard)
      btnRotinaCard.addEventListener("click", executarRotinaCompleta);

    // Atualizar serviços
    var btnServicos = document.getElementById("btn-atualizar-servicos");
    if (btnServicos) btnServicos.addEventListener("click", carregarServicos);

    // Liberar RAM
    document.getElementById('btn-liberar-ram')?.addEventListener('click', async () => {
      mostrarOverlay('Liberando memória RAM standby...', true);
      try {
        const jobRes = await bridge.call("liberar_memoria_standby");
        const res = await window.awaitJob(jobRes.job_id);
        esconderOverlay(true, res?.ok);
      } catch(e) { esconderOverlay(true, false); }
    });

    // Analisar Startup
    document.getElementById('btn-analisar-startup')?.addEventListener('click', async () => {
      mostrarOverlay('Analisando programas de inicialização...');
      try {
        const jobRes = await bridge.call("analisar_startup");
        const res = await window.awaitJob(jobRes.job_id);
        esconderOverlay();
        if (res?.ok && res.entradas) {
          const container = document.getElementById('resultado-startup');
          container.style.display = 'block';
          container.innerHTML = `
            <div class="card">
              <strong style="color:var(--cor-primaria)">
                ${res.entradas.length} programas encontrados no startup
              </strong>
              <table class="tabela-dados" style="margin-top:16px">
                <thead>
                  <tr>
                    <th>Programa</th>
                    <th>Origem</th>
                  </tr>
                </thead>
                <tbody>
                  ${res.entradas.map(e => `
                    <tr>
                      <td>${e.nome}</td>
                      <td>
                        <span class="badge ${e.raiz === 'HKLM' ? 'alerta' : 'neutro'}">
                          ${e.raiz}
                        </span>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
              <p class="texto-secundario" style="margin-top:12px">
                💡 Use o Gerenciador de Tarefas (Ctrl+Shift+Esc → 
                Inicializar) para desativar programas desnecessários.
              </p>
            </div>
          `;
        }
      } catch(e) { esconderOverlay(); }
    });
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
