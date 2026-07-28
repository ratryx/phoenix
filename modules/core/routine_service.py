import os
import traceback
from modules import logs
from modules import diagnostico
from modules import limpeza
from modules import otimizacao
from modules import relatorio

class RoutineService:
    def __init__(self, svc_diagnostico=None, svc_limpeza=None, svc_otimizacao=None, svc_logs=None, svc_relatorio=None):
        self.diagnostico = svc_diagnostico or diagnostico
        self.limpeza = svc_limpeza or limpeza
        self.otimizacao = svc_otimizacao or otimizacao
        self.logs = svc_logs or logs
        self.relatorio = svc_relatorio or relatorio

    def executar(self, id_atendimento: str, nome_cliente: str, job_context=None) -> dict:
        if not id_atendimento:
            return {"ok": False, "erro": "O ID do atendimento é obrigatório"}

        def check_cancel():
            if job_context:
                job_context.raise_if_cancelled()

        try:
            self.logs.registrar_acao(id_atendimento, "Início da rotina completa")
            check_cancel()

            # Passo 1: Diagnostico Inicial
            if job_context:
                job_context.update_progress(10, "Realizando diagnóstico inicial...")
            diag_inicial = self.diagnostico.coletar_diagnostico_silencioso()
            check_cancel()

            # Passo 2: Limpeza
            if job_context:
                job_context.update_progress(30, "Executando limpeza completa...")
            bytes_liberados = self.limpeza.executar_limpeza_completa(id_atendimento)
            check_cancel()

            # Passo 3: Otimizacao
            if job_context:
                job_context.update_progress(60, "Aplicando otimizações gerais e de gaming...")
            self.otimizacao.executar_otimizacao_geral(id_atendimento)
            check_cancel()

            self.otimizacao.ativar_plano_energia_alto_desempenho()
            self.otimizacao.ativar_modo_jogo_windows()
            self.otimizacao.desativar_gamebar_overlay()
            self.otimizacao.otimizar_gpu_para_jogos()
            check_cancel()

            # Passo 4: Diagnostico Final
            if job_context:
                job_context.update_progress(80, "Realizando diagnóstico final...")
            diag_final = self.diagnostico.coletar_diagnostico_silencioso()
            check_cancel()

            # Passo 5: Relatorio
            if job_context:
                job_context.update_progress(90, "Gerando relatório final...")
            caminho_relatorio = self.relatorio.gerar_pdf(id_atendimento, nome_cliente, diag_inicial, diag_final, bytes_liberados)
            check_cancel()

            self.logs.registrar_acao(id_atendimento, "Rotina concluída com sucesso")

            if job_context:
                job_context.update_progress(100, "Concluído!")

            return {
                "ok": True,
                "relatorio_gerado": os.path.exists(caminho_relatorio) if caminho_relatorio else False,
                "caminho_relatorio": caminho_relatorio,
                "espaco_liberado_mb": round(bytes_liberados / (1024**2), 2)
            }

        except Exception as e:
            msg_erro = str(e)
            if "Job cancelled cooperatively" in msg_erro:
                self.logs.registrar_acao(id_atendimento, "Rotina cancelada pelo usuário")
                return {
                    "ok": False,
                    "codigo": "JOB_CANCELLED",
                    "erro": "Rotina cancelada cooperativamente."
                }
            self.logs.registrar_acao(id_atendimento, f"Erro na rotina: {msg_erro}")
            traceback.print_exc()
            return {
                "ok": False,
                "erro": msg_erro
            }
