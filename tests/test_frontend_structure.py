import os
from pathlib import Path

def test_arquivos_existem():
    base = Path("gui/js")
    assert (base / "core/namespace.js").exists()
    assert (base / "core/state.js").exists()
    assert (base / "core/bridge.js").exists()
    assert (base / "core/jobs.js").exists()
    assert (base / "core/lifecycle.js").exists()
    assert (base / "core/router.js").exists()
    assert (base / "ui/feedback.js").exists()

def test_ordem_carregamento():
    conteudo = Path("gui/index.html").read_text(encoding="utf-8")
    scripts = [
        "js/core/namespace.js",
        "js/core/state.js",
        "js/core/bridge.js",
        "js/ui/feedback.js",
        "js/core/jobs.js",
        "js/core/lifecycle.js",
        "js/core/router.js",
        "app.js"
    ]
    
    posicoes = []
    for script in scripts:
        idx = conteudo.find(f'src="{script}"')
        assert idx != -1, f"Script {script} não encontrado no index.html"
        posicoes.append(idx)
        
    # Verifica ordem
    assert posicoes == sorted(posicoes), "Scripts não estão carregando na ordem esperada"

def test_ausencia_es_modules():
    conteudo = Path("gui/index.html").read_text(encoding="utf-8")
    assert 'type="module"' not in conteudo, "ES Modules detectados no index.html"
    
    js_files = list(Path("gui").rglob("*.js"))
    for js in js_files:
        c = js.read_text(encoding="utf-8")
        assert "import " not in c and "export " not in c, f"Sintaxe ES module detectada em {js}"

def test_bridge_isolada():
    js_files = list(Path("gui").rglob("*.js"))
    for js in js_files:
        c = js.read_text(encoding="utf-8")
        if js.name == "bridge.js":
            assert "window.pywebview.api" in c, "bridge.js não acessa window.pywebview.api"
        else:
            assert "window.pywebview.api" not in c, f"Vazamento da bridge direta em {js.name}"

def test_state_isolado():
    c = Path("gui/app.js").read_text(encoding="utf-8")
    assert "Phoenix.state = {" not in c, "STATE sendo redeclarado no app.js"

def test_await_job_isolado():
    c = Path("gui/app.js").read_text(encoding="utf-8")
    assert "function awaitJob(" not in c, "awaitJob reimplementado no app.js"

def test_listener_unico():
    js_files = list(Path("gui").rglob("*.js"))
    ocorrencias = 0
    for js in js_files:
        c = js.read_text(encoding="utf-8")
        ocorrencias += c.count('addEventListener("pywebviewready"')
    assert ocorrencias == 1, "Múltiplos listeners pywebviewready detectados"

def test_ausencia_alert_confirm():
    js_files = list(Path("gui").rglob("*.js"))
    for js in js_files:
        c = js.read_text(encoding="utf-8")
        # Ensure we aren't matching word boundaries or comments.
        import re
        # Removes comments for safe check
        c_no_comments = re.sub(r'//.*', '', c)
        assert not re.search(r'\balert\(', c_no_comments), f"alert() detectado em {js}"
        assert not re.search(r'\bconfirm\(', c_no_comments), f"confirm() detectado em {js}"

def test_utilizacao_phoenix():
    js_files = list(Path("gui").rglob("*.js"))
    for js in js_files:
        c = js.read_text(encoding="utf-8")
        assert "Phoenix" in c, f"Módulo {js.name} não parece usar o namespace Phoenix"
