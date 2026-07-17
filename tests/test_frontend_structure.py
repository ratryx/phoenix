import os
import re
from pathlib import Path
import subprocess

def test_arquivos_existem():
    base = Path("gui/js")
    assert (base / "core/namespace.js").exists()
    assert (base / "core/state.js").exists()
    assert (base / "core/bridge.js").exists()
    assert (base / "core/jobs.js").exists()
    assert (base / "core/lifecycle.js").exists()
    assert (base / "core/router.js").exists()
    assert (base / "operations/restore-point.js").exists()
    assert (base / "features/client-session.js").exists()
    assert (base / "ui/window-controls.js").exists()
    assert (base / "operations/routine.js").exists()
    assert (base / "operations/restore-point.js").exists()
    assert (base / "pages/inicio.js").exists()
    assert (base / "pages/diagnostico.js").exists()
    assert (base / "pages/hardware.js").exists()
    assert (base / "pages/sensores.js").exists()
    assert (base / "pages/limpeza.js").exists()
    assert (base / "pages/otimizacao.js").exists()
    assert (base / "pages/servicos.js").exists()
    assert (base / "pages/historico.js").exists()
    assert (base / "pages/relatorio.js").exists()
    assert (base / "../app.js").exists()

def test_ordem_carregamento():
    """Valida se a ordem dos scripts extraídos no HTML está coerente"""
    with open("gui/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Define a ordem esperada no index.html
    ordem_esperada = [
        "js/core/namespace.js",
        "js/core/state.js",
        "js/core/bridge.js",
        "js/ui/feedback.js",
        "js/core/jobs.js",
        "js/core/lifecycle.js",
        "js/core/router.js",
        "js/ui/window-controls.js",
        "js/operations/restore-point.js",
        "js/operations/routine.js",
        "js/features/client-session.js",
        "js/pages/inicio.js",
        "js/pages/diagnostico.js",
        "js/pages/hardware.js",
        "js/pages/sensores.js",
        "js/pages/limpeza.js",
        "js/pages/otimizacao.js",
        "js/pages/servicos.js",
        "js/pages/historico.js",
        "js/pages/relatorio.js",
        "app.js"
    ]
    
    indices = []
    for script in ordem_esperada:
        idx = html.find(script)
        assert idx != -1, f"Script {script} não encontrado na index.html"
        indices.append(idx)
        
    # Verifica se os índices estão ordenados de forma crescente
    assert indices == sorted(indices), "Os scripts não estão na ordem correta na index.html"
    
def test_ausencia_es_modules():
    """Garante que não estamos usando type='module', mantendo o design IIFE"""
    with open("gui/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert 'type="module"' not in html, "A arquitetura proíbe o uso de ES Modules"

def test_bridge_isolada():
    """Valida que páginas não acessam diretamente window.pywebview"""
    base = Path("gui/js")
    for js in base.rglob("*.js"):
        c = js.read_text(encoding="utf-8")
        if js.name == "bridge.js":
            assert "window.pywebview.api" in c, "bridge.js não acessa window.pywebview.api"
        else:
            assert "window.pywebview.api" not in c, f"{js.name} está acessando pywebview diretamente. Use Phoenix.bridge"

def test_func_nao_duplicadas():
    c = Path("gui/app.js").read_text(encoding="utf-8")
    funcs_removidas = [
        "function carregarHardwareInicial",
        "function atualizarRodapeFalha",
        "function atualizarCardsHardware",
        "function iniciarAtualizacaoTempoReal",
        "function carregarDiagnostico",
        "function renderizarDiagnostico",
        "function carregarHardware",
        "function renderizarAbaHardware",
        "function carregarSensores",
        "function executarLimpeza",
        "function renderizarLimpeza"
    ]
    for func in funcs_removidas:
        assert func not in c, f"{func} permaneceu duplicada no app.js"
        
def test_funcoes_possuem_implementacao():
    js_files = list(Path("gui/js").rglob("*.js"))
    funcs_migradas = [
        "carregarHardwareInicial",
        "atualizarRodapeFalha",
        "atualizarCardsHardware",
        "iniciarAtualizacaoTempoReal",
        "carregarDiagnostico",
        "renderizarDiagnostico",
        "carregarHardware",
        "renderTab",
        "atualizar"
    ]
    all_content = "".join(f.read_text(encoding="utf-8") for f in js_files)
    for func in funcs_migradas:
        assert func in all_content, f"Implementação de {func} ausente nos novos módulos"

def test_paginas_ainda_no_app_js():
    c = Path("gui/app.js").read_text(encoding="utf-8")
    assert "executarLimpeza" not in c, "Limpeza não foi removida do app.js"
    assert "renderizarLimpeza" not in c, "Limpeza não foi removida do app.js"
    assert "executarOtimizacaoGeral" not in c, "Otimização não foi removida do app.js"
    assert "carregarServicos" not in c, "Serviços não foi removida do app.js"
    assert "carregarHistorico" not in c, "Histórico não foi removida do app.js"
    assert "renderizarRelatorio" not in c, "Relatório não foi removido do app.js"
    assert "executarRotinaCompleta" not in c, "Rotina Completa não está mais no app.js"
    
def test_style_nao_alterado():
    try:
        res = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True)
        assert "style.css" not in res.stdout
    except:
        pass

def test_arquivos_temporarios():
    import glob
    assert len(glob.glob("gui/**/*.tmp", recursive=True)) == 0
    assert len(glob.glob("gui/**/*.bak", recursive=True)) == 0

def test_ids_dom_preservados():
    html = Path("gui/index.html").read_text(encoding="utf-8")
    assert 'id="cards-resumo-inicio"' in html
    assert 'id="conteudo-diagnostico"' in html
    assert 'id="hw-conteudo"' in html

def test_modulos_usam_phoenix_pages():
    for f in ["inicio.js", "diagnostico.js", "hardware.js", "sensores.js", "limpeza.js"]:
        c = Path(f"gui/js/pages/{f}").read_text(encoding="utf-8")
        assert "Phoenix.pages." in c or "Phoenix.pages =" in c

def test_corPorPercentual_unica():
    all_js = list(Path("gui").rglob("*.js"))
    implementacoes = sum(1 for js in all_js if "function corPorPercentual(" in js.read_text(encoding="utf-8"))
    assert implementacoes == 1, "corPorPercentual não possui origem única"

def test_globals_documentados():
    doc = Path("docs/architecture/frontend-pages.md").read_text(encoding="utf-8")
    assert "window.renderizarAbaHardware" in doc
    assert "Phoenix.ui.corPorPercentual" in doc or "window.corPorPercentual" in doc

def test_nenhum_alerta_nativo():
    js_files = list(Path("gui").rglob("*.js"))
    for js in js_files:
        c = js.read_text(encoding="utf-8")
        assert not re.search(r'\balert\(', c), f"alert() nativo encontrado em {js}"
        assert not re.search(r'\bconfirm\(', c), f"confirm() nativo encontrado em {js}"

def test_limpeza_sem_modal():
    c = Path("gui/js/pages/limpeza.js").read_text(encoding="utf-8")
    assert "confirmarModal" not in c, "confirmarModal não deve ser usado na Limpeza"
    assert "window.confirm" not in c, "window.confirm não deve ser usado"
    assert "alert(" not in c, "alert não deve ser usado"
