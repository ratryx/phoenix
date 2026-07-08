/* ============================================================
   Phoenix Optimizer — GUI Frontend Logic
   Toda chamada de funcionalidade real (diagnóstico, limpeza,
   otimização, serviços) vai para pywebview.api.<metodo>, que
   delega ao mesmo núcleo Python usado pelo modo CLI.
   ============================================================ */

let hardwareDetectado = null;
let nivelQualidadeVisual = "media";

// ---------- Utilidades ----------

function formatarBytes(mb) {
  if (mb >= 1024) return (mb / 1024).toFixed(2) + " GB";
  return mb.toFixed(1) + " MB";
}

function corPorPercentual(pct) {
  if (pct >= 85) return "erro";
  if (pct >= 65) return "alerta";
  return "";
}

function mostrarOverlay(texto) {
  document.getElementById("texto-overlay").textContent = texto;
  document.getElementById("overlay-processando").classList.add("visivel");
}

function ocultarOverlay() {
  document.getElementById("overlay-processando").classList.remove("visivel");
}

async function chamarAPI(metodo, ...args) {
  if (!window.pywebview || !window.pywebview.api) {
    console.warn("pywebview.api ainda não disponível");
    return { ok: false, erro: "API não disponível" };
  }
  return await window.pywebview.api[metodo](...args);
}

async function executarComPolling(apiCallPromise, callbackConcluido) {
  try {
    const resInicial = await apiCallPromise;
    if (!resInicial || !resInicial.job_id) {
      console.error("Retorno inválido da API, job_id ausente:", resInicial);
      ocultarOverlay();
      return;
    }
    
    const jobId = resInicial.job_id;
    const poll = setInterval(async () => {
      if (window.pywebview && window.pywebview.api) {
        try {
          const estado = await window.pywebview.api.verificar_tarefa(jobId);
          if (estado.status === 'done') {
            clearInterval(poll);
            callbackConcluido(estado.resultado);
          } else if (estado.status === 'not_found') {
            clearInterval(poll);
            console.error("Tarefa não encontrada:", jobId);
            ocultarOverlay();
          }
        } catch (e) {
          clearInterval(poll);
          console.error("Erro ao verificar tarefa:", e);
          ocultarOverlay();
        }
      }
    }, 500);
  } catch (e) {
    console.error("Erro ao iniciar tarefa:", e);
    ocultarOverlay();
  }
}

// ---------- Navegação entre páginas ----------

function irParaPagina(idPagina) {
  document.querySelectorAll(".pagina").forEach(p => p.classList.remove("ativa"));
  document.querySelectorAll(".item-menu").forEach(m => m.classList.remove("ativo"));

  const pagina = document.getElementById("pagina-" + idPagina);
  if (pagina) pagina.classList.add("ativa");

  const itemMenu = document.querySelector(`.item-menu[data-pagina="${idPagina}"]`);
  if (itemMenu) itemMenu.classList.add("ativo");
}

document.querySelectorAll(".item-menu[data-pagina]").forEach(item => {
  item.addEventListener("click", () => {
    const destino = item.dataset.pagina;
    irParaPagina(destino);
    if (destino === "hardware") carregarHardware();
    if (destino === "servicos") carregarServicos();
    if (destino === "historico") carregarHistorico();
  });
});

// ---------- Qualidade visual adaptativa ----------

function aplicarNivelQualidade(nivel) {
  nivelQualidadeVisual = nivel;
  document.body.classList.remove("qualidade-alta", "qualidade-media", "qualidade-baixa");

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
  const camada = document.getElementById("camada-particulas");
  if (!camada) return;
  camada.innerHTML = "";

  const quantidade = 14;
  for (let i = 0; i < quantidade; i++) {
    const p = document.createElement("div");
    p.className = "particula";
    const tamanho = 4 + Math.random() * 10;
    p.style.width = tamanho + "px";
    p.style.height = tamanho + "px";
    p.style.left = Math.random() * 100 + "%";
    p.style.top = (60 + Math.random() * 40) + "%";
    p.style.animationDuration = (8 + Math.random() * 10) + "s";
    p.style.animationDelay = (Math.random() * 10) + "s";
    camada.appendChild(p);
  }
}

// ---------- Inicialização ----------

window.addEventListener("pywebviewready", async () => {
  const resultadoHw = await chamarAPI("obter_hardware");
  hardwareDetectado = resultadoHw;

  const nivel = await chamarAPI("obter_nivel_qualidade_visual");
  aplicarNivelQualidade(nivel);

  preencherResumoInicio(hardwareDetectado, nivel);
  preencherRodapeHardware(hardwareDetectado);
});

function preencherResumoInicio(hw, nivel) {
  if (!hw) return;
  const cards = document.getElementById("cards-resumo-inicio");
  const cpu = hw.cpu, ram = hw.ram, gpus = hw.gpus || [];

  cards.innerHTML = `
    <div class="card-metrica">
      <div class="rotulo">CPU</div>
      <div class="valor">${cpu.uso_percentual}<span class="unidade">%</span></div>
      <div class="barra-progresso"><div class="preenchimento ${corPorPercentual(cpu.uso_percentual)}" style="width:${cpu.uso_percentual}%"></div></div>
    </div>
    <div class="card-metrica">
      <div class="rotulo">Memória RAM</div>
      <div class="valor">${ram.percentual_uso}<span class="unidade">%</span></div>
      <div class="barra-progresso"><div class="preenchimento ${corPorPercentual(ram.percentual_uso)}" style="width:${ram.percentual_uso}%"></div></div>
    </div>
    <div class="card-metrica">
      <div class="rotulo">GPU</div>
      <div class="valor" style="font-size:16px">${gpus.length > 0 ? gpus[0].nome : "Não detectada"}</div>
    </div>
    <div class="card-metrica">
      <div class="rotulo">Modo gráfico recomendado</div>
      <div class="valor" style="font-size:16px; text-transform:capitalize">${nivel}</div>
    </div>
  `;
}

function preencherRodapeHardware(hw) {
  if (!hw) return;
  const rodape = document.getElementById("rodape-hardware");
  rodape.innerHTML = `${hw.cpu.nucleos_logicos} núcleos · ${hw.ram.total_gb} GB RAM`;
}

// ---------- Diagnóstico ----------

document.getElementById("btn-atualizar-diagnostico").addEventListener("click", carregarDiagnostico);

function carregarDiagnostico() {
  mostrarOverlay("Coletando diagnóstico...");
  executarComPolling(chamarAPI("obter_diagnostico"), window.onDiagnosticoConcluido);
}

window.onDiagnosticoConcluido = (resultado) => {
  ocultarOverlay();
  const container = document.getElementById("conteudo-diagnostico");

  if (!resultado.ok) {
    container.innerHTML = `<div class="card"><span class="badge erro">Erro</span> ${resultado.erro}</div>`;
    return;
  }

  const d = resultado.dados;
  const discosHtml = d.discos.map(disco => `
    <tr>
      <td>${disco.unidade}</td>
      <td>${disco.total_gb} GB</td>
      <td>${disco.usado_gb} GB</td>
      <td>${disco.livre_gb} GB</td>
      <td><span class="badge ${corPorPercentual(disco.percentual_uso) || 'neutro'}">${disco.percentual_uso}%</span></td>
    </tr>
  `).join("");

  const processosHtml = d.processos.slice(0, 8).map(p => `
    <tr>
      <td>${p.name || "desconhecido"}</td>
      <td>${(p.cpu_percent || 0).toFixed(1)}%</td>
      <td>${(p.memory_percent || 0).toFixed(1)}%</td>
    </tr>
  `).join("");

  container.innerHTML = `
    <div class="grade-cards">
      <div class="card-metrica">
        <div class="rotulo">CPU</div>
        <div class="valor">${d.cpu.uso_percentual}<span class="unidade">%</span></div>
      </div>
      <div class="card-metrica">
        <div class="rotulo">RAM em uso</div>
        <div class="valor">${d.memoria.percentual_uso}<span class="unidade">%</span></div>
      </div>
      <div class="card-metrica">
        <div class="rotulo">RAM disponível</div>
        <div class="valor">${d.memoria.disponivel_gb}<span class="unidade">GB</span></div>
      </div>
    </div>

    <div class="card">
      <strong>Armazenamento</strong>
      <table class="tabela-dados" style="margin-top:12px">
        <thead><tr><th>Unidade</th><th>Total</th><th>Usado</th><th>Livre</th><th>Uso</th></tr></thead>
        <tbody>${discosHtml}</tbody>
      </table>
    </div>

    <div class="card">
      <strong>Processos com maior consumo</strong>
      <table class="tabela-dados" style="margin-top:12px">
        <thead><tr><th>Processo</th><th>CPU</th><th>RAM</th></tr></thead>
        <tbody>${processosHtml}</tbody>
      </table>
    </div>
  `;
}

// ---------- Hardware ----------

async function carregarHardware() {
  const container = document.getElementById("conteudo-hardware");
  if (!hardwareDetectado) {
    container.innerHTML = `<p class="texto-secundario">Detectando hardware...</p>`;
    return;
  }

  const cpu = hardwareDetectado.cpu, ram = hardwareDetectado.ram, gpus = hardwareDetectado.gpus || [];

  let gpusHtml = `<p class="texto-secundario">Nenhuma GPU detectada.</p>`;
  if (gpus.length > 0) {
    gpusHtml = gpus.map(gpu => `
      <div class="card">
        <strong>${gpu.nome}</strong>
        <table class="tabela-dados" style="margin-top:12px">
          <tbody>
            <tr><td>Fabricante</td><td>${gpu.fabricante || "—"}</td></tr>
            ${gpu.vram_total_mb ? `<tr><td>VRAM total</td><td>${(gpu.vram_total_mb / 1024).toFixed(1)} GB</td></tr>` : ""}
            ${gpu.vram_usada_mb !== null && gpu.vram_usada_mb !== undefined ? `<tr><td>VRAM em uso</td><td>${(gpu.vram_usada_mb / 1024).toFixed(1)} GB</td></tr>` : ""}
            ${gpu.uso_percentual !== null && gpu.uso_percentual !== undefined ? `<tr><td>Uso atual</td><td>${gpu.uso_percentual}%</td></tr>` : ""}
            ${gpu.temperatura_c !== null && gpu.temperatura_c !== undefined ? `<tr><td>Temperatura</td><td>${gpu.temperatura_c}°C</td></tr>` : ""}
            ${gpu.driver_versao ? `<tr><td>Driver</td><td>${gpu.driver_versao}</td></tr>` : ""}
          </tbody>
        </table>
      </div>
    `).join("");
  }

  container.innerHTML = `
    <div class="card">
      <strong>Processador</strong>
      <table class="tabela-dados" style="margin-top:12px">
        <tbody>
          <tr><td>Modelo</td><td>${cpu.modelo}</td></tr>
          <tr><td>Núcleos físicos / lógicos</td><td>${cpu.nucleos_fisicos} / ${cpu.nucleos_logicos}</td></tr>
          <tr><td>Uso atual</td><td>${cpu.uso_percentual}%</td></tr>
        </tbody>
      </table>
    </div>
    <div class="card">
      <strong>Memória RAM</strong>
      <table class="tabela-dados" style="margin-top:12px">
        <tbody>
          <tr><td>Total</td><td>${ram.total_gb} GB</td></tr>
          <tr><td>Disponível</td><td>${ram.disponivel_gb} GB</td></tr>
          <tr><td>Uso atual</td><td>${ram.percentual_uso}%</td></tr>
        </tbody>
      </table>
    </div>
    ${gpusHtml}
  `;
}

// ---------- Limpeza ----------

document.getElementById("btn-executar-limpeza").addEventListener("click", () => {
  mostrarOverlay("Limpando arquivos temporários...");
  executarComPolling(chamarAPI("executar_limpeza"), window.onLimpezaConcluida);
});

window.onLimpezaConcluida = (resultado) => {
  ocultarOverlay();
  const container = document.getElementById("conteudo-limpeza");
  if (!resultado.ok) {
    container.innerHTML = `<div class="card"><span class="badge erro">Erro</span> ${resultado.erro}</div>`;
    return;
  }

  container.innerHTML = `
    <div class="card">
      <span class="badge sucesso">Concluído</span>
      <p style="margin-top:10px">Espaço total liberado: <strong>${formatarBytes(resultado.espaco_liberado_mb)}</strong></p>
    </div>
  `;
};

// ---------- Modal de Confirmação do Ponto de Restauração ----------

let restorePointCreatedThisSession = false;
let acaoPendenteAposRestauracao = null;

function exibirModalRestauracao(titulo, mensagem, tipo, aoConfirmar, aoCancelar) {
  const modal = document.getElementById("modal-restauracao");
  const tituloEl = document.getElementById("modal-titulo");
  const mensagemEl = document.getElementById("modal-mensagem");
  const iconEl = document.getElementById("modal-icon");
  const btnConfirmar = document.getElementById("btn-modal-confirmar");
  const btnCancelar = document.getElementById("btn-modal-cancelar");

  tituloEl.textContent = titulo;
  mensagemEl.textContent = mensagem;

  // Reset classes e ícone
  iconEl.className = "modal-status-icon " + tipo;
  if (tipo === "sucesso") {
    iconEl.textContent = "✓";
  } else if (tipo === "erro" || tipo === "alerta") {
    iconEl.textContent = "⚠";
  }

  // Ajustar textos e classes dos botões
  if (tipo === "sucesso") {
    btnConfirmar.textContent = "Confirmar e Prosseguir";
    btnConfirmar.className = "botao primario";
  } else {
    btnConfirmar.textContent = "Continuar mesmo assim";
    btnConfirmar.className = "botao primario";
  }
  btnCancelar.textContent = "Cancelar";

  // Event handlers
  const cliqueConfirmar = () => {
    modal.classList.remove("visivel");
    desregistrarEventos();
    aoConfirmar();
  };

  const cliqueCancelar = () => {
    modal.classList.remove("visivel");
    desregistrarEventos();
    aoCancelar();
  };

  function desregistrarEventos() {
    btnConfirmar.removeEventListener("click", cliqueConfirmar);
    btnCancelar.removeEventListener("click", cliqueCancelar);
  }

  btnConfirmar.addEventListener("click", cliqueConfirmar);
  btnCancelar.addEventListener("click", cliqueCancelar);

  modal.classList.add("visivel");
}

function comPontoRestauracao(acaoConfirmada) {
  if (restorePointCreatedThisSession) {
    acaoConfirmada();
    return;
  }

  acaoPendenteAposRestauracao = acaoConfirmada;
  mostrarOverlay("Criando ponto de restauração do sistema...");
  executarComPolling(chamarAPI("criar_ponto_restauracao"), window.onCriarPontoRestauracaoConcluido);
}

window.onCriarPontoRestauracaoConcluido = (res) => {
  ocultarOverlay();

  if (res.ok) {
    restorePointCreatedThisSession = true;
    exibirModalRestauracao(
      "Ponto de Restauração Criado",
      res.mensagem || "O ponto de restauração foi criado com sucesso. Deseja prosseguir com as otimizações?",
      "sucesso",
      () => {
        if (acaoPendenteAposRestauracao) acaoPendenteAposRestauracao();
      },
      () => { acaoPendenteAposRestauracao = null; }
    );
  } else {
    if (res.codigo === "NO_ADMIN") {
      exibirModalRestauracao(
        "Permissão Negada",
        res.erro || "Privilégios de Administrador insuficientes para criar pontos de restauração e aplicar otimizações.",
        "erro",
        () => {},
        () => { acaoPendenteAposRestauracao = null; }
      );
      // Ocultamos o botão de confirmar mesmo assim
      document.getElementById("btn-modal-confirmar").style.display = "none";
      const restaurarBotao = () => {
        document.getElementById("btn-modal-confirmar").style.display = "";
        document.getElementById("btn-modal-cancelar").removeEventListener("click", restaurarBotao);
      };
      document.getElementById("btn-modal-cancelar").addEventListener("click", restaurarBotao);
    } else {
      exibirModalRestauracao(
        "Falha na Restauração",
        `Não foi possível criar o ponto de restauração: ${res.erro}. Deseja aplicar as otimizações mesmo assim?`,
        "alerta",
        () => {
          restorePointCreatedThisSession = true;
          if (acaoPendenteAposRestauracao) acaoPendenteAposRestauracao();
        },
        () => { acaoPendenteAposRestauracao = null; }
      );
    }
  }
};

// ---------- Otimização ----------

document.getElementById("btn-otimizacao-geral").addEventListener("click", () => {
  comPontoRestauracao(() => {
    mostrarOverlay("Aplicando otimização geral...");
    executarComPolling(chamarAPI("executar_otimizacao_geral"), window.onOtimizacaoGeralConcluida);
  });
});

window.onOtimizacaoGeralConcluida = (resultado) => {
  ocultarOverlay();
  exibirResultadoOtimizacao(resultado, "Otimização geral aplicada.");
};

document.getElementById("btn-otimizacao-gaming").addEventListener("click", () => {
  comPontoRestauracao(() => {
    mostrarOverlay("Aplicando otimização para jogos...");
    executarComPolling(chamarAPI("executar_otimizacao_gaming", false), window.onOtimizacaoGamingConcluida);
  });
});

window.onOtimizacaoGamingConcluida = (resultado) => {
  ocultarOverlay();
  exibirResultadoOtimizacao(resultado, "Otimização para jogos aplicada. Reinicie o PC para garantir efeito completo.");
};

document.getElementById("btn-otimizar-disco").addEventListener("click", () => {
  mostrarOverlay("Otimizando disco — isso pode levar alguns minutos...");
  executarComPolling(chamarAPI("otimizar_disco"), window.onOtimizarDiscoConcluido);
});

window.onOtimizarDiscoConcluido = (resultado) => {
  ocultarOverlay();
  exibirResultadoOtimizacao(resultado, "Otimização de disco concluída.");
};

function exibirResultadoOtimizacao(resultado, mensagemSucesso) {
  const container = document.getElementById("resultado-otimizacao");
  if (!resultado.ok) {
    container.innerHTML = `<div class="card"><span class="badge erro">Erro</span> ${resultado.erro}</div>`;
    return;
  }
  container.innerHTML = `<div class="card"><span class="badge sucesso">Concluído</span> ${mensagemSucesso}</div>`;
}

// ---------- Serviços ----------

async function carregarServicos() {
  const container = document.getElementById("conteudo-servicos");
  container.innerHTML = `<p class="texto-secundario">Consultando serviços...</p>`;

  const resultado = await chamarAPI("listar_servicos");
  if (!resultado.ok) {
    container.innerHTML = `<div class="card"><span class="badge erro">Erro</span> ${resultado.erro}</div>`;
    return;
  }

  const linhas = resultado.servicos.map(s => {
    const ativo = s.status === "Rodando";
    return `
      <tr>
        <td>
          <strong>${s.nome_amigavel}</strong>
          <div class="texto-terciario">${s.descricao}</div>
        </td>
        <td><span class="badge ${ativo ? 'sucesso' : 'neutro'}">${s.status}</span></td>
        <td>
          <div class="toggle ${ativo ? 'ativo' : ''}" data-servico="${s.nome_servico}" data-ativo="${ativo}">
            <div class="bola"></div>
          </div>
        </td>
      </tr>
    `;
  }).join("");

  container.innerHTML = `
    <div class="card">
      <table class="tabela-dados">
        <thead><tr><th>Serviço</th><th>Status</th><th>Ação</th></tr></thead>
        <tbody>${linhas}</tbody>
      </table>
    </div>
  `;

  let activeToggle = null;

  window.onServicoToggleConcluido = (resultado) => {
    ocultarOverlay();
    const toggle = activeToggle;
    if (resultado.ok && toggle) {
      const estaAtivo = toggle.dataset.ativo === "true";
      toggle.classList.toggle("ativo");
      toggle.dataset.ativo = (!estaAtivo).toString();
    }
    activeToggle = null;
  };

  container.querySelectorAll(".toggle").forEach(toggle => {
    toggle.addEventListener("click", () => {
      const nomeServico = toggle.dataset.servico;
      const estaAtivo = toggle.dataset.ativo === "true";

      comPontoRestauracao(() => {
        mostrarOverlay(estaAtivo ? "Desativando serviço..." : "Ativando serviço...");
        activeToggle = toggle;
        const metodoAcao = estaAtivo ? "desativar_servico" : "ativar_servico";
        executarComPolling(chamarAPI(metodoAcao, nomeServico), window.onServicoToggleConcluido);
      });
    });
  });
}

document.getElementById("btn-atualizar-servicos").addEventListener("click", carregarServicos);

// ---------- Histórico ----------

async function carregarHistorico() {
  const container = document.getElementById("conteudo-historico");
  container.innerHTML = `<p class="texto-secundario">Carregando histórico...</p>`;

  const resultado = await chamarAPI("obter_historico");
  if (!resultado.ok) {
    container.innerHTML = `<div class="card"><span class="badge erro">Erro</span> ${resultado.erro}</div>`;
    return;
  }

  if (resultado.atendimentos.length === 0) {
    container.innerHTML = `<p class="texto-secundario">Nenhum atendimento registrado ainda.</p>`;
    return;
  }

  const linhas = resultado.atendimentos.map(a => `
    <tr>
      <td>${a.id_atendimento}</td>
      <td>${a.cliente}</td>
      <td>${a.data_hora}</td>
    </tr>
  `).join("");

  container.innerHTML = `
    <div class="card">
      <table class="tabela-dados">
        <thead><tr><th>ID</th><th>Cliente</th><th>Data/Hora</th></tr></thead>
        <tbody>${linhas}</tbody>
      </table>
    </div>
  `;
}

// ---------- Rotina completa ----------

async function executarRotinaCompleta() {
  comPontoRestauracao(() => {
    mostrarOverlay("Executando rotina completa — isso pode levar alguns minutos...");
    executarComPolling(chamarAPI("executar_rotina_completa", ""), window.onRotinaCompletaConcluida);
  });
}

window.onRotinaCompletaConcluida = (resultado) => {
  ocultarOverlay();

  if (!resultado.ok) {
    alert("Erro ao executar rotina completa: " + resultado.erro);
    return;
  }

  irParaPagina("relatorio");
  renderizarRelatorio(resultado);
};

function renderizarRelatorio(resultado) {
  const container = document.getElementById("conteudo-relatorio");
  const antes = resultado.antes, depois = resultado.depois;

  function linhaComparativa(rotulo, valorAntes, valorDepois, sufixo, menorEMelhor) {
    const diferenca = valorDepois - valorAntes;
    const melhorou = menorEMelhor ? diferenca < 0 : diferenca > 0;
    const corDif = Math.abs(diferenca) < 0.01 ? "neutro" : (melhorou ? "sucesso" : "erro");
    const seta = Math.abs(diferenca) < 0.01 ? "=" : (melhorou ? "\u25BC" : "\u25B2");
    return `
      <tr>
        <td>${rotulo}</td>
        <td>${valorAntes}${sufixo}</td>
        <td>${valorDepois}${sufixo}</td>
        <td><span class="badge ${corDif}">${seta} ${Math.abs(diferenca).toFixed(1)}${sufixo}</span></td>
      </tr>
    `;
  }

  container.innerHTML = `
    <div class="grade-cards">
      <div class="card-metrica">
        <div class="rotulo">Espaço liberado</div>
        <div class="valor">${formatarBytes(resultado.espaco_liberado_mb)}</div>
      </div>
    </div>

    <div class="card">
      <strong>CPU & memória — antes vs depois</strong>
      <table class="tabela-dados" style="margin-top:12px">
        <thead><tr><th>Métrica</th><th>Antes</th><th>Depois</th><th>Variação</th></tr></thead>
        <tbody>
          ${linhaComparativa("Uso de CPU", antes.cpu.uso_percentual, depois.cpu.uso_percentual, "%", true)}
          ${linhaComparativa("Uso de RAM", antes.memoria.percentual_uso, depois.memoria.percentual_uso, "%", true)}
          ${linhaComparativa("RAM disponível", antes.memoria.disponivel_gb, depois.memoria.disponivel_gb, " GB", false)}
        </tbody>
      </table>
    </div>

    <div class="card">
      <span class="badge sucesso">Relatório exportado</span>
      <p class="texto-secundario" style="margin-top:8px">${resultado.relatorio_txt}</p>
    </div>
  `;
}

document.getElementById("btn-rotina-completa").addEventListener("click", executarRotinaCompleta);
document.getElementById("btn-rotina-completa-card").addEventListener("click", executarRotinaCompleta);

// ---------- Controles da janela ----------

document.getElementById("btn-minimizar").addEventListener("click", () => chamarAPI("minimizar_janela"));
document.getElementById("btn-fechar").addEventListener("click", () => chamarAPI("fechar_janela"));


// ---------- Arrastar janela frameless (drag) ----------

let estaArrastando = false;
let dragConfigurado = false;
let ultimoX = 0;
let ultimoY = 0;
let animFrameId = null;

function processarMovimento() {
  if (estaArrastando && window.pywebview && window.pywebview.api) {
    window.pywebview.api.mover_janela(ultimoX, ultimoY);
    animFrameId = requestAnimationFrame(processarMovimento);
  } else {
    animFrameId = null;
  }
}

function configurarDragJanela() {
  if (dragConfigurado) return;
  
  const elementosDrag = [];
  
  // Titlebar principal
  const titlebar = document.querySelector(".barra-titulo");
  if (titlebar) elementosDrag.push(titlebar);
  
  // Todos os cabeçalhos de página (e.g., .cabecalho-pagina)
  document.querySelectorAll(".cabecalho-pagina").forEach(el => elementosDrag.push(el));
  
  elementosDrag.forEach(el => {
    el.addEventListener("mousedown", (e) => {
      if (e.target.closest("button") || e.target.closest("input") || e.target.closest("a") || e.target.closest(".controles-janela")) {
        return;
      }
      estaArrastando = true;
      ultimoX = e.screenX;
      ultimoY = e.screenY;
      const winX = e.screenX - e.clientX;
      const winY = e.screenY - e.clientY;
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.iniciar_drag(e.screenX, e.screenY, winX, winY);
      }
      if (!animFrameId) {
        animFrameId = requestAnimationFrame(processarMovimento);
      }
    });
  });

  window.addEventListener("mousemove", (e) => {
    if (estaArrastando) {
      ultimoX = e.screenX;
      ultimoY = e.screenY;
    }
  });

  window.addEventListener("mouseup", () => {
    if (estaArrastando) {
      estaArrastando = false;
      if (animFrameId) {
        cancelAnimationFrame(animFrameId);
        animFrameId = null;
      }
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.parar_drag();
      }
    }
  });
  
  dragConfigurado = true;
}

// Inicializar drag
document.addEventListener("DOMContentLoaded", configurarDragJanela);
// Executar de imediato caso o DOM já esteja pronto
if (document.readyState === "complete" || document.readyState === "interactive") {
  configurarDragJanela();
}
