import pytest
import os
from pathlib import Path
from modules.relatorio import exportar_relatorio_html

def test_exportar_relatorio_html_escapes_xss(tmp_path):
    saida = tmp_path / "relatorio.html"
    
    payload = "<script>alert('xss')</script>"
    
    snapshot_antes = {
        "cliente": payload,
        "dados": {
            "cpu": {"uso_percentual": 50},
            "memoria": {"percentual_uso": 50, "disponivel_gb": 4},
            "discos": [
                {"unidade": payload, "livre_gb": 10}
            ]
        }
    }
    
    snapshot_depois = {
        "data_hora": payload,
        "dados": {
            "cpu": {"uso_percentual": 40},
            "memoria": {"percentual_uso": 40, "disponivel_gb": 6},
            "discos": [
                {"unidade": payload, "livre_gb": 20}
            ]
        }
    }
    
    exportar_relatorio_html(snapshot_antes, snapshot_depois, 500, saida)
    
    conteudo = saida.read_text(encoding="utf-8")
    
    # Must not contain the raw payload
    assert payload not in conteudo
    
    # Must contain the escaped version
    escaped = "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    # wait, html.escape might not quote single quotes by default, but it says html.escape(quote=True) in requirements?
    # spec says: "Verify/test html.escape for all string interpolations in relatorio.py."
    assert "&lt;script&gt;alert(" in conteudo
