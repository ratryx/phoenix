import logging
from modules.core.exceptions import JobCancelledError

logger = logging.getLogger(__name__)

class RoutineService:
    """
    Serviço dedicado para orquestrar a rotina completa de atendimento.
    Isola a lógica de negócio do PhoenixAPI e garante que a sequência
    de diagnóstico, limpeza, otimização e geração de relatórios seja
    cumprida e validada independentemente de janelas ou threads.
    """
    def __init__(
        self,
        diagnostico_module=None,
        limpeza_module=None,
        otimizacao_module=None,
        logs_module=None,
        relatorio_module=None,
    ):
        # Injeção de dependências (usa os reais por padrão)
        if diagnostico_module is None:
            from modules import diagnostico
            diagnostico_module = diagnostico
        if limpeza_module is None:
            from modules import limpeza
            limpeza_module = limpeza
        if otimizacao_module is None:
            from modules import otimizacao
            otimizacao_module = otimizacao
        if logs_module is None:
            from modules import logs
            logs_module = logs
        if relatorio_module is None:
            from modules import relatorio
            relatorio_module = relatorio

        self._diagnostico = diagnostico_module
        self._limpeza = limpeza_module
        self._otimizacao = otimizacao_module
        self._logs = logs_module
        self._relatorio = relatorio_module

    def executar(self, id_atendimento: str, nome_cliente: str = "", job_context=None) -> dict:
        """
        Executa o fluxo completo do atendimento:
        1. Diagnóstico Inicial
        2. Limpeza
        3. Otimização
        4. Diagnóstico Final
        5. Exportação de Relatório
        """
        if not id_atendimento:
            raise ValueError("ID do atendimento é obrigatório para iniciar a rotina.")

        def check_cancel():
            if job_context:
                job_context.raise_if_cancelled()

        try:
            # Checkpoint 1: before initial diagnosis
            check_cancel()
            if job_context: job_context.update_progress(10, "Realizando diagnóstico inicial...")
            
            # 1. Diagnóstico Inicial
            dados_antes = self._diagnostico.coletar_diagnostico_silencioso()
            self._logs.salvar_snapshot(id_atendimento, "antes", dados_antes, nome_cliente)
            self._logs.registrar_acao(id_atendimento, "Diagnóstico inicial coletado", nome_cliente=nome_cliente)
            
            # Checkpoint 2: after initial diagnosis and snapshot persistence
            check_cancel()

            # Checkpoint 3: before cleanup
            check_cancel()
            if job_context: job_context.update_progress(30, "Executando limpeza completa...")
            
            # 2. Limpeza
            espaco_liberado = self._limpeza.executar_limpeza_completa(id_atendimento)
            
            # Checkpoint 4: after cleanup
            check_cancel()

            # Checkpoint 5: before optimization
            check_cancel()
            if job_context: job_context.update_progress(60, "Aplicando otimizações gerais...")
            
            # 3. Otimização
            self._otimizacao.executar_otimizacao_geral(id_atendimento)
            
            # Checkpoint 6: after optimization
            check_cancel()

            # Checkpoint 7: before final diagnosis
            check_cancel()
            if job_context: job_context.update_progress(80, "Realizando diagnóstico final...")
            
            # 4. Diagnóstico Final
            dados_depois = self._diagnostico.coletar_diagnostico_silencioso()
            self._logs.salvar_snapshot(id_atendimento, "depois", dados_depois, nome_cliente)
            self._logs.registrar_acao(id_atendimento, "Diagnóstico final coletado")
            
            # Checkpoint 8: after final snapshot persistence
            check_cancel()

            # Checkpoint 9: before report generation
            check_cancel()
            if job_context: job_context.update_progress(90, "Gerando relatório final...")
            
            # 5. Exportação de Relatório
            espaco_liberado_mb = round(espaco_liberado / (1024 ** 2), 2)
            pasta_logs = self._logs.obter_pasta_logs()
            caminho_txt = pasta_logs / f"{id_atendimento}_relatorio.txt"
            
            snapshot_antes = self._logs.carregar_snapshot(id_atendimento, "antes")
            snapshot_depois = self._logs.carregar_snapshot(id_atendimento, "depois")
            
            self._relatorio.exportar_relatorio_txt(snapshot_antes, snapshot_depois, espaco_liberado_mb, caminho_txt)

            self._logs.registrar_acao(id_atendimento, "Rotina concluída com sucesso")
            if job_context: job_context.update_progress(100, "Concluído!")

            return {
                "ok": True,
                "id_atendimento": id_atendimento,
                "antes": dados_antes,
                "depois": dados_depois,
                "espaco_liberado_mb": espaco_liberado_mb,
                "relatorio_txt": str(caminho_txt),
            }

        except JobCancelledError:
            self._logs.registrar_acao(id_atendimento, "Rotina cancelada pelo usuário")
            return {
                "ok": False,
                "codigo": "JOB_CANCELLED",
                "erro": "Rotina cancelada cooperativamente."
            }
        except Exception as e:
            self._logs.registrar_acao(id_atendimento, f"Erro na rotina: {e}")
            logger.exception("Falha inesperada durante a rotina completa.")
            return {
                "ok": False,
                "codigo": "ROUTINE_FAILED",
                "erro": "Não foi possível concluir a rotina."
            }
