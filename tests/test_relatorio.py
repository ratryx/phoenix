import pytest
import os
from pathlib import Path
from modules.relatorio import exportar_relatorio_html, exportar_relatorio_txt

def test_exportar_relatorio_html_escapes_xss(tmp_path):
    saida = tmp_path / "relatorio.html"

    payload = "<script>alert('xss')</script>"

    snapshot_antes = {
        "dados": {
            "cpu": {"uso_percentual": 50},
            "memoria": {"percentual_uso": 50, "disponivel_gb": 4},
            "discos": [
                {"unidade": payload, "livre_gb": 10}
            ]
        }
    }

    snapshot_depois = {
        "dados": {
            "cpu": {"uso_percentual": 40},
            "memoria": {"percentual_uso": 40, "disponivel_gb": 6},
            "discos": [
                {"unidade": payload, "livre_gb": 20}
            ]
        }
    }

    payload_mock = {
        "cliente": payload,
        "data_hora": payload,
        "resumo": {"espaco_liberado_mb": 500},
        "limpeza": {"categorias": []},
        "otimizacoes": {},
        "protecao": {},
        "analises": {},
        "recomendacoes": []
    }

    exportar_relatorio_html(payload_mock, snapshot_antes, snapshot_depois, saida)

    conteudo = saida.read_text(encoding="utf-8")

    # Must not contain the raw payload
    assert payload not in conteudo

    # Must contain the escaped version
    escaped = "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    assert "&lt;script&gt;alert(" in conteudo

def test_exportar_relatorio_txt_v2(tmp_path):
    saida_txt = tmp_path / 'relatorio.txt'
    saida_html = tmp_path / 'relatorio.html'

    snapshot_antes = {'cliente': 'Teste', 'dados': {'cpu': {'uso_percentual': 50}, 'memoria': {'percentual_uso': 50, 'disponivel_gb': 4}, 'discos': [{'unidade': 'C:', 'livre_gb': 10}]}}
    snapshot_depois = {'data_hora': '2026-08-08 12:00:00', 'dados': {'cpu': {'uso_percentual': 40}, 'memoria': {'percentual_uso': 40, 'disponivel_gb': 6}, 'discos': [{'unidade': 'C:', 'livre_gb': 20}]}}

    payload_mock = {
        'duracao_segundos': 120,
        'resumo': {
            'espaco_liberado_mb': 500,
            'itens_removidos': 1500,
            'otimizacoes_aplicadas': 4,
            'otimizacoes_total': 5
        },
        'limpeza': {
            'categorias': [{'nome': 'Temp', 'arquivos_removidos': 1000, 'espaco_liberado_bytes': 300*1024*1024, 'status': 'concluido'}]
        },
        'otimizacoes': {
            'total': 5,
            'sucessos': 4,
            'resultados': {'ServicoA': {'ok': True, 'descricao': 'Servico A'}}
        },
        'protecao': {'status': 'restore_created'},
        'analises': {},
        'recomendacoes': []
    }

    exportar_relatorio_txt(payload_mock, snapshot_antes, snapshot_depois, saida_txt)
    exportar_relatorio_html(payload_mock, snapshot_antes, snapshot_depois, saida_html)

    assert saida_txt.exists()
    assert saida_html.exists()

    conteudo_txt = saida_txt.read_text(encoding='utf-8')
    assert 'Espaço liberado: 500.00 MB' in conteudo_txt
    assert 'Otimizações aplicadas: 4 de 5' in conteudo_txt
    assert 'Status de proteção: Ponto de restauração criado e verificado' in conteudo_txt

def test_exportar_relatorio_txt_before_state_contract(tmp_path):
    saida_txt = tmp_path / 'relatorio_before_state.txt'
    snapshot_antes = {'cliente': 'Teste', 'dados': {'cpu': {'uso_percentual': 50}, 'memoria': {'percentual_uso': 50, 'disponivel_gb': 4}, 'discos': [{'unidade': 'C:', 'livre_gb': 10}]}}
    snapshot_depois = snapshot_antes

    payload_mock = {
        'otimizacoes': {
            'before_state': {
                'plano_energia': {'ativo': False, 'descricao': 'Plano'},
                'modo_jogo': {'ativo': True, 'descricao': 'Modo Jogo'}
            },
            'resultados': {
                'plano_energia': {'ok': True, 'descricao': 'Plano'},
                'modo_jogo': {'ok': True, 'descricao': 'Modo Jogo'},
                'sem_estado': {'ok': True, 'descricao': 'Sem Estado'}
            }
        },
    }

    exportar_relatorio_txt(payload_mock, snapshot_antes, snapshot_depois, saida_txt)

    conteudo = saida_txt.read_text(encoding='utf-8')
    assert "Antes: Não aplicado | Ação: Otimizar | Resultado: APLICADO" in conteudo
    assert "Antes: Já aplicado | Ação: Otimizar | Resultado: APLICADO" in conteudo
    assert "- Sem Estado -> APLICADO" in conteudo
