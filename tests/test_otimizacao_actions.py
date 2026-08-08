import pytest
from unittest.mock import patch
from modules.otimizacao import reaplicar_todas_inativas, executar_otimizacao_geral, executar_otimizacao_gaming, criar_ponto_restauracao

@patch("modules.otimizacao.criar_ponto_restauracao")
@patch("modules.otimizacao.reaplicar_otimizacao")
def test_reaplicar_todas_inativas_falhas(mock_reaplicar, mock_pr):
    mock_pr.return_value = {"ok": True}
    mock_reaplicar.side_effect = [
        {"ok": True, "id": "modo_jogo"},
        {"ok": False, "id": "gpu_scheduling"}
    ]
    status_atual = {
        "itens": [
            {"ativo": False, "id": "modo_jogo"},
            {"ativo": False, "id": "gpu_scheduling"}
        ]
    }
    res = reaplicar_todas_inativas(status_atual)
    assert res == {"ok": False, "codigo": "OPERATION_PARTIAL_FAILURE", "reaplicadas": ["modo_jogo"], "falhas": ["gpu_scheduling"]}

@patch("modules.otimizacao.is_admin")
@patch("modules.otimizacao.run_windows_command")
@patch("modules.otimizacao.obter_ultimo_restore_point_sequence")
def test_criar_ponto_restauracao_cancelled(mock_seq, mock_run, mock_admin):
    mock_admin.return_value = True
    mock_seq.return_value = {"ok": True, "sequence": 0}
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(
        ok=False, code="COMMAND_CANCELLED", returncode=None, stdout="", stderr="",
        timed_out=False, cancelled=True, duration_ms=10, termination_ok=True
    )
    res = criar_ponto_restauracao()
    assert res == {"ok": False, "codigo": "COMMAND_CANCELLED", "erro": "A operação foi cancelada pelo usuário."}

@patch("modules.otimizacao.ativar_plano_energia_alto_desempenho")
@patch("modules.otimizacao.desativar_efeitos_visuais")
@patch("modules.otimizacao.limitar_processos_em_segundo_plano")
@patch("modules.logs.registrar_acao")
def test_executar_otimizacao_geral_partial(mock_log, mock_limitar, mock_efeitos, mock_plano):
    mock_plano.return_value = {"ok": True, "codigo": "COMMAND_OK"}
    mock_efeitos.return_value = {"ok": False, "codigo": "COMMAND_FAILED"}
    mock_limitar.return_value = {"ok": True, "codigo": "COMMAND_OK"}

    res = executar_otimizacao_geral(id_atendimento="123")
    assert res["ok"] is False
    assert res["codigo"] == "OPERATION_PARTIAL_FAILURE"
    mock_log.assert_called_with("123", "Otimização geral concluída parcialmente", "2/3 sucessos")

@patch("modules.otimizacao.ativar_plano_energia_alto_desempenho")
@patch("modules.otimizacao.ativar_modo_jogo_windows")
@patch("modules.otimizacao.desativar_gamebar_overlay")
@patch("modules.otimizacao.otimizar_gpu_para_jogos")
@patch("modules.logs.registrar_acao")
def test_executar_otimizacao_gaming_partial(mock_log, mock_gpu, mock_gamebar, mock_modo_jogo, mock_plano):
    mock_plano.return_value = {"ok": True, "codigo": "COMMAND_OK"}
    mock_modo_jogo.return_value = {"ok": False, "codigo": "COMMAND_FAILED"}
    mock_gamebar.return_value = {"ok": True, "codigo": "COMMAND_OK"}
    mock_gpu.return_value = {"ok": True, "codigo": "COMMAND_OK"}

    res = executar_otimizacao_gaming(id_atendimento="123")
    assert res["ok"] is False
    assert res["codigo"] == "OPERATION_PARTIAL_FAILURE"
    mock_log.assert_called_with("123", "Otimização para jogos concluída parcialmente", "3/4 sucessos")

@patch("modules.otimizacao.is_admin", return_value=True)
@patch("modules.otimizacao.obter_ultimo_restore_point_sequence")
@patch("modules.otimizacao.run_windows_command")
@patch("modules.otimizacao._verificar_ponto_restauracao_especifico")
def test_criar_ponto_restauracao_no_existing_success(mock_verif, mock_run, mock_seq, mock_admin):
    mock_seq.return_value = {"ok": True, "sequence": 0}
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=True, code="COMMAND_OK", returncode=0, stdout="", stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    mock_verif.return_value = True

    res = criar_ponto_restauracao()
    assert res["ok"] is True
    mock_verif.assert_called_with(0, 'Phoenix Optimizer - Pré-Otimização')

@patch("modules.otimizacao.is_admin", return_value=True)
@patch("modules.otimizacao.obter_ultimo_restore_point_sequence")
@patch("modules.otimizacao.run_windows_command")
@patch("modules.otimizacao._verificar_ponto_restauracao_especifico")
def test_criar_ponto_restauracao_existing_success(mock_verif, mock_run, mock_seq, mock_admin):
    mock_seq.return_value = {"ok": True, "sequence": 15}
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=True, code="COMMAND_OK", returncode=0, stdout="", stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    mock_verif.return_value = True

    res = criar_ponto_restauracao()
    assert res["ok"] is True
    mock_verif.assert_called_with(15, 'Phoenix Optimizer - Pré-Otimização')

@patch("modules.otimizacao.is_admin", return_value=True)
@patch("modules.otimizacao.obter_ultimo_restore_point_sequence")
def test_criar_ponto_restauracao_before_query_failure(mock_seq, mock_admin):
    mock_seq.return_value = {"ok": False, "codigo": "RESTORE_QUERY_FAILED", "erro": "Falha simulada"}
    res = criar_ponto_restauracao()
    assert res["ok"] is False
    assert res["codigo"] == "RESTORE_QUERY_FAILED"

@patch("modules.otimizacao.is_admin", return_value=True)
@patch("modules.otimizacao.obter_ultimo_restore_point_sequence")
@patch("modules.otimizacao.run_windows_command")
@patch("modules.otimizacao._verificar_ponto_restauracao_especifico")
def test_criar_ponto_restauracao_after_query_failure(mock_verif, mock_run, mock_seq, mock_admin):
    mock_seq.return_value = {"ok": True, "sequence": 10}
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=True, code="COMMAND_OK", returncode=0, stdout="", stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    # _verificar_ponto_restauracao_especifico retorna false quando falha ou não encontra
    mock_verif.return_value = False

    res = criar_ponto_restauracao()
    assert res["ok"] is False
    assert res["codigo"] == "RESTORE_VERIFICATION_FAILED"

@patch("modules.otimizacao.is_admin", return_value=True)
@patch("modules.otimizacao.obter_ultimo_restore_point_sequence")
@patch("modules.otimizacao.run_windows_command")
def test_criar_ponto_restauracao_command_failure(mock_run, mock_seq, mock_admin):
    mock_seq.return_value = {"ok": True, "sequence": 5}
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=False, code="COMMAND_FAILED", returncode=1, stdout="", stderr="access denied", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)

    res = criar_ponto_restauracao()
    assert res["ok"] is False
    assert res["codigo"] == "NO_ADMIN"

@patch("modules.otimizacao.is_admin", return_value=True)
@patch("modules.otimizacao.obter_ultimo_restore_point_sequence")
@patch("modules.otimizacao.run_windows_command")
@patch("modules.otimizacao._verificar_ponto_restauracao_especifico")
def test_criar_ponto_restauracao_unrelated_point_appearing(mock_verif, mock_run, mock_seq, mock_admin):
    mock_seq.return_value = {"ok": True, "sequence": 5}
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=True, code="COMMAND_OK", returncode=0, stdout="", stderr="", timed_out=False, cancelled=False, duration_ms=100, termination_ok=True)
    # Mesmo se o comando rodou, se a query nao encontra o nosso (encontrou de outro software)
    mock_verif.return_value = False

    res = criar_ponto_restauracao()
    assert res["ok"] is False
    assert res["codigo"] == "RESTORE_VERIFICATION_FAILED"

from modules.otimizacao import _verificar_ponto_restauracao_especifico

@patch('modules.otimizacao.run_windows_command')
def test_verificar_ponto_restauracao_especifico_found(mock_run):
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=True, code='COMMAND_OK', returncode=0, stdout='FOUND', stderr='', timed_out=False, cancelled=False, duration_ms=10, termination_ok=True)
    assert _verificar_ponto_restauracao_especifico(5, 'Teste') is True

@patch('modules.otimizacao.run_windows_command')
def test_verificar_ponto_restauracao_especifico_found_newline(mock_run):
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=True, code='COMMAND_OK', returncode=0, stdout='FOUND\r\n', stderr='', timed_out=False, cancelled=False, duration_ms=10, termination_ok=True)
    assert _verificar_ponto_restauracao_especifico(5, 'Teste') is True

@patch('modules.otimizacao.run_windows_command')
def test_verificar_ponto_restauracao_especifico_not_found(mock_run):
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=True, code='COMMAND_OK', returncode=0, stdout='NOT_FOUND', stderr='', timed_out=False, cancelled=False, duration_ms=10, termination_ok=True)
    assert _verificar_ponto_restauracao_especifico(5, 'Teste') is False

@patch('modules.otimizacao.run_windows_command')
def test_verificar_ponto_restauracao_especifico_empty(mock_run):
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=True, code='COMMAND_OK', returncode=0, stdout='', stderr='', timed_out=False, cancelled=False, duration_ms=10, termination_ok=True)
    assert _verificar_ponto_restauracao_especifico(5, 'Teste') is False

@patch('modules.otimizacao.run_windows_command')
def test_verificar_ponto_restauracao_especifico_failure(mock_run):
    from modules.core.windows_command import CommandResult
    mock_run.return_value = CommandResult(ok=False, code='COMMAND_FAILED', returncode=1, stdout='FOUND', stderr='', timed_out=False, cancelled=False, duration_ms=10, termination_ok=True)
    assert _verificar_ponto_restauracao_especifico(5, 'Teste') is False
