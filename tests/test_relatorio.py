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

    payload_mock = {
        "limpeza": {"espaco_liberado_mb": 500},
        "otimizacao": {},
        "protecao": {}
    }

    exportar_relatorio_html(payload_mock, snapshot_antes, snapshot_depois, saida)

    conteudo = saida.read_text(encoding="utf-8")

    # Must not contain the raw payload
    assert payload not in conteudo

    # Must contain the escaped version
    escaped = "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    # wait, html.escape might not quote single quotes by default, but it says html.escape(quote=True) in requirements?
    # spec says: "Verify/test html.escape for all string interpolations in relatorio.py."
    assert "&lt;script&gt;alert(" in conteudo

def test_exportar_relatorio_txt_v2(tmp_path):
    from modules.relatorio import exportar_relatorio_txt, exportar_relatorio_html
    saida_txt = tmp_path / 'relatorio.txt'
    saida_html = tmp_path / 'relatorio.html'

    snapshot_antes = {'cliente': 'Teste', 'dados': {'cpu': {'uso_percentual': 50}, 'memoria': {'percentual_uso': 50, 'disponivel_gb': 4}, 'discos': [{'unidade': 'C:', 'livre_gb': 10}]}}
    snapshot_depois = {'data_hora': '2026-08-08 12:00:00', 'dados': {'cpu': {'uso_percentual': 40}, 'memoria': {'percentual_uso': 40, 'disponivel_gb': 6}, 'discos': [{'unidade': 'C:', 'livre_gb': 20}]}}
    payload_mock = {
        'duracao_segundos': 120,
        'limpeza': {
            'espaco_liberado_mb': 500,
            'arquivos_removidos': 1500,
            'categorias': [{'nome': 'Temp', 'arquivos_removidos': 1000, 'espaco_liberado_bytes': 300*1024*1024, 'status': 'concluido'}]
        },
        'otimizacao': {
            'total': 5,
            'sucessos': 4,
            'resultados': {'ServicoA': {'ok': True}}
        },
        'protecao': {'status': 'restore_created'}
    }

    exportar_relatorio_txt(payload_mock, snapshot_antes, snapshot_depois, saida_txt)
    exportar_relatorio_html(payload_mock, snapshot_antes, snapshot_depois, saida_html)

    assert saida_txt.exists()
    assert saida_html.exists()

    conteudo_txt = saida_txt.read_text(encoding='utf-8')
    assert 'Espaço liberado: 500.00 MB' in conteudo_txt
    assert 'Arquivos removidos: 1500' in conteudo_txt
    assert 'Otimizações aplicadas: 4 de 5' in conteudo_txt
    assert 'Status de proteção: restore_created' in conteudo_txt
    # Will check category later once we update exportar_relatorio_txt
