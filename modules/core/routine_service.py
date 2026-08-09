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
        cleanup_service_module=None,
        otimizacao_module=None,
        logs_module=None,
        relatorio_module=None,
        smart_module=None,
        driver_module=None,
    ):
        # Injeção de dependências (usa os reais por padrão)
        if diagnostico_module is None:
            from modules import diagnostico
            diagnostico_module = diagnostico
        if cleanup_service_module is None:
            from modules.core import cleanup_service
            cleanup_service_module = cleanup_service
        if otimizacao_module is None:
            from modules import otimizacao
            otimizacao_module = otimizacao
        if logs_module is None:
            from modules import logs
            logs_module = logs
        if relatorio_module is None:
            from modules import relatorio
            relatorio_module = relatorio
        if smart_module is None:
            from modules import smart
            smart_module = smart
        if driver_module is None:
            from modules import driver_check
            driver_module = driver_check

        self._diagnostico = diagnostico_module
        self._limpeza = cleanup_service_module
        self._otimizacao = otimizacao_module
        self._logs = logs_module
        self._relatorio = relatorio_module
        self._smart = smart_module
        self._driver = driver_module

    def executar(self, id_atendimento: str, nome_cliente: str = "Desconhecido", job_context=None, protection_state=None) -> dict:
        """
        Orquestra a rotina completa V2:
        1. Diagnóstico Inicial
        2. Limpeza Segura
        3. Otimizações Seguras
        4. Análise de Inicialização
        5. Saúde dos Discos (SMART)
        6. Análise de Drivers
        7. Otimização Condicional de Discos
        8. Diagnóstico Final
        9. Relatório V3
        """
        from datetime import datetime
        t_start = datetime.now()
        if not id_atendimento:
            raise ValueError("ID do atendimento é obrigatório para iniciar a rotina.")

        def check_cancel():
            if job_context:
                job_context.raise_if_cancelled()

        try:
            # 1. Diagnóstico Inicial (Blocking)
            check_cancel()
            if job_context: job_context.update_progress(5, "Diagnosticando sistema (inicial)...")
            dados_antes = self._diagnostico.coletar_diagnostico_silencioso()
            dados_antes["cliente"] = nome_cliente
            self._logs.salvar_snapshot(id_atendimento, "antes", dados_antes, nome_cliente)
            self._logs.registrar_acao(id_atendimento, "Diagnóstico inicial coletado", nome_cliente=nome_cliente)
            
            # 2. Validation Protection
            check_cancel()
            if job_context: job_context.update_progress(10, "Validando proteção do sistema...")
            
            # 3. Limpeza (Non-blocking)
            check_cancel()
            if job_context: job_context.update_progress(15, "Executando limpeza profunda...")
            def cleanup_progress(mensagem, progresso, detalhes):
                if job_context:
                    job_context.update_progress(15 + int(progresso * 0.25), mensagem, details=detalhes) # 15-40
            try:
                limpeza_resultado = self._limpeza.executar_limpeza(
                    progress_callback=cleanup_progress,
                    cancel_event=job_context.cancel_event if job_context else None,
                    incluir_lixeira=False
                )
                espaco_liberado_mb = limpeza_resultado.get("espaco_liberado_mb", 0.0)
                self._logs.registrar_acao(id_atendimento, "Limpeza executada", f"{espaco_liberado_mb} MB liberados", nome_cliente=nome_cliente)
            except JobCancelledError:
                raise
            except Exception as e:
                logger.exception("Falha não-bloqueante na limpeza.")
                limpeza_resultado = {"espaco_liberado_mb": 0.0, "categorias": [], "codigo": "CLEANUP_FAILED", "erro": "A limpeza não pôde ser concluída."}

            # 4. Otimizações Gerais (Non-blocking)
            check_cancel()
            if job_context: job_context.update_progress(45, "Aplicando otimizações seguras...")
            try:
                optimization_result = self._otimizacao.executar_otimizacao_geral(
                    id_atendimento,
                    cancel_event=job_context.cancel_event if job_context else None,
                )
                if optimization_result.get("codigo") == "COMMAND_CANCELLED":
                    raise JobCancelledError()
            except JobCancelledError:
                raise
            except Exception as e:
                logger.exception("Falha não-bloqueante na otimização.")
                optimization_result = {"sucessos": 0, "total": 0, "resultados": {}, "ok": False, "codigo": "OPTIMIZATION_FAILED", "erro": "Falha ao aplicar otimizações."}

            # 5. Startup Analysis (Non-blocking)
            check_cancel()
            if job_context: job_context.update_progress(55, "Analisando entradas de inicialização...")
            startup_result = {"entradas": [], "total": 0, "alto_impacto": 0, "ok": False}
            try:
                entradas = self._otimizacao.analisar_startup()
                startup_result["entradas"] = entradas
                startup_result["total"] = len(entradas)
                heavy_keywords = ["onedrive", "epicgames", "steam", "discord", "spotify", "skype", "webex", "teams", "origin", "riotclient"]
                high_impact = sum(1 for e in entradas if any(k in str(e.get("comando", "")).lower() for k in heavy_keywords))
                startup_result["alto_impacto"] = high_impact
                startup_result["ok"] = True
            except JobCancelledError:
                raise
            except Exception as e:
                logger.exception("Falha não-bloqueante na análise de inicialização.")
                startup_result["codigo"] = "STARTUP_ANALYSIS_FAILED"
                startup_result["erro"] = "Não foi possível analisar os itens de inicialização."

            # 6. Disk Health SMART (Non-blocking)
            check_cancel()
            if job_context: job_context.update_progress(65, "Verificando saúde dos discos (SMART)...")
            smart_result = {"discos": [], "ok": False}
            try:
                discos = self._smart.coletar_saude_discos()
                smart_result["discos"] = discos
                if not discos:
                    smart_result["ok"] = False
                    smart_result["codigo"] = "SMART_UNAVAILABLE"
                    smart_result["erro"] = "Não foi possível consultar a saúde dos discos."
                else:
                    smart_result["ok"] = True
            except JobCancelledError:
                raise
            except Exception as e:
                logger.exception("Falha não-bloqueante no SMART.")
                smart_result["codigo"] = "SMART_UNAVAILABLE"
                smart_result["erro"] = "Não foi possível consultar a saúde dos discos."

            # 7. Driver Analysis (Non-blocking)
            check_cancel()
            if job_context: job_context.update_progress(75, "Verificando integridade dos drivers...")
            driver_result = {"resultados": [], "ok": False}
            try:
                dr_res = self._driver.executar_verificacao_drivers(cancel_event=job_context.cancel_event if job_context else None)
                if dr_res.get("codigo") == "COMMAND_CANCELLED":
                    raise JobCancelledError()
                driver_result["resultados"] = dr_res.get("itens", [])
                driver_result["ok"] = dr_res.get("ok", False)
            except JobCancelledError:
                raise
            except Exception as e:
                logger.exception("Falha não-bloqueante nos drivers.")
                driver_result["codigo"] = "DRIVERS_UNAVAILABLE"
                driver_result["erro"] = "Falha ao verificar atualizações de driver."

            # 8. Disk Optimization (Normal Optimization Phase)
            check_cancel()
            if job_context: job_context.update_progress(85, "Otimizando armazenamento (SSD/HDD)...")
            try:
                res_disco = self._otimizacao.otimizar_disco_principal(cancel_event=job_context.cancel_event if job_context else None)
                if res_disco.get("codigo") == "COMMAND_CANCELLED":
                    raise JobCancelledError()
                
                # Append to optimization_result
                if optimization_result.get("resultados") is not None:
                    optimization_result["resultados"]["otimizacao_disco"] = {
                        "ok": res_disco.get("ok", False),
                        "descricao": "Otimização de Armazenamento",
                        "detalhe": res_disco.get("saida", res_disco.get("erro", ""))
                    }
                    if res_disco.get("ok"):
                        optimization_result["sucessos"] = optimization_result.get("sucessos", 0) + 1
                    optimization_result["total"] = optimization_result.get("total", 0) + 1
            except JobCancelledError:
                raise
            except Exception as e:
                logger.exception("Falha não-bloqueante na otimização de disco.")
                if optimization_result.get("resultados") is not None:
                    optimization_result["resultados"]["otimizacao_disco"] = {
                        "ok": False,
                        "descricao": "Otimização de Armazenamento",
                        "detalhe": "Falha ao otimizar o armazenamento.",
                        "codigo": "DISK_OPT_FAILED"
                    }
                    optimization_result["total"] = optimization_result.get("total", 0) + 1

            # 9. Diagnóstico Final (Blocking)
            check_cancel()
            if job_context: job_context.update_progress(92, "Diagnosticando sistema (final)...")
            dados_depois = self._diagnostico.coletar_diagnostico_silencioso()
            self._logs.salvar_snapshot(id_atendimento, "depois", dados_depois, nome_cliente)
            self._logs.registrar_acao(id_atendimento, "Diagnóstico final coletado")

            # 10. Geração de Relatório
            check_cancel()
            if job_context: job_context.update_progress(97, "Gerando Relatório Profissional V3...")

            duracao = (datetime.now() - t_start).total_seconds()
            
            payload = {
                "ok": True,
                "id_atendimento": id_atendimento,
                "duracao_segundos": int(duracao),
                "resumo": {
                    "espaco_liberado_mb": limpeza_resultado.get("espaco_liberado_mb", 0.0),
                    "itens_removidos": sum((c.get("arquivos_removidos", 0) for c in limpeza_resultado.get("categorias", []))),
                    "otimizacoes_aplicadas": optimization_result.get("sucessos", 0),
                    "otimizacoes_total": optimization_result.get("total", 0),
                    "recomendacoes_encontradas": 0
                },
                "antes": dados_antes,
                "depois": dados_depois,
                "limpeza": limpeza_resultado,
                "otimizacoes": optimization_result,
                "analises": {
                    "startup": startup_result,
                    "smart": smart_result,
                    "drivers": driver_result
                },
                "acoes_condicionais": {},
                "protecao": protection_state or {"status": "unknown", "mensagem": "Não tentado"}
            }

            self._gerar_recomendacoes_deterministicas(payload)
            payload["resumo"]["recomendacoes_encontradas"] = len(payload.get("recomendacoes", []))

            pasta_logs = self._logs.obter_pasta_logs()
            caminho_txt = pasta_logs / f"{id_atendimento}_relatorio.txt"
            caminho_html = pasta_logs / f"{id_atendimento}_relatorio.html"
            payload["relatorio_txt"] = str(caminho_txt)
            payload["relatorio_html"] = str(caminho_html)

            self._relatorio.exportar_relatorio_txt(payload, dados_antes, dados_depois, caminho_txt)
            self._relatorio.exportar_relatorio_html(payload, dados_antes, dados_depois, caminho_html)

            self._logs.registrar_acao(id_atendimento, "Rotina concluída com sucesso")
            if job_context: job_context.update_progress(100, "Rotina Completa finalizada.")

            return payload

        except JobCancelledError:
            self._logs.registrar_acao(id_atendimento, "Rotina cancelada pelo usuário")
            raise
        except Exception as e:
            self._logs.registrar_acao(id_atendimento, "Falha durante a execução da rotina completa")
            logger.exception("Falha inesperada durante a rotina completa.")
            return {
                "ok": False,
                "codigo": "ROUTINE_FAILED",
                "erro": "Não foi possível concluir a rotina."
            }

    def _gerar_recomendacoes_deterministicas(self, payload: dict):
        recs = []
        
        # 1. Startup
        startup = payload.get("analises", {}).get("startup", {})
        if startup.get("ok") and (startup.get("total", 0) > 15 or startup.get("alto_impacto", 0) > 0):
            recs.append({
                "codigo": "STARTUP_HIGH_IMPACT",
                "nivel": "aviso",
                "titulo": "Programas de Inicialização",
                "descricao": f"Foram detectados {startup.get('alto_impacto', 0)} programas de alto impacto ou excesso de itens no boot. Considere revisar a aba Otimização."
            })

        # 2. Disk Health
        smart = payload.get("analises", {}).get("smart", {})
        if smart.get("ok"):
            discos = smart.get("discos", [])
            if any(d.get("health_status", "").lower() not in ["healthy", "saudável"] for d in discos):
                recs.append({
                    "codigo": "DISK_HEALTH_WARNING",
                    "nivel": "erro",
                    "titulo": "Saúde do Disco",
                    "descricao": "Atenção crítica à saúde de um ou mais discos. Considere realizar um backup imediatamente e providenciar a substituição do componente."
                })

        # 3. Disk Space
        dados_depois = payload.get("depois", {})
        discos_depois = dados_depois.get("discos", [])
        if any(d.get("livre_gb", 100) < 15.0 for d in discos_depois):
            recs.append({
                "codigo": "DISK_SPACE_LOW",
                "nivel": "erro",
                "titulo": "Espaço em Disco Crítico",
                "descricao": "Uma ou mais unidades estão com menos de 15 GB de espaço livre, o que pode causar lentidão severa. Considere expandir o armazenamento."
            })

        # 4. Drivers
        drivers = payload.get("analises", {}).get("drivers", {})
        if drivers.get("ok") and any(d.get("classificacao") in ["Desatualizado", "Aviso"] for d in drivers.get("resultados", [])):
            recs.append({
                "codigo": "DRIVER_REVIEW_RECOMMENDED",
                "nivel": "aviso",
                "titulo": "Revisão de Drivers",
                "descricao": "Atualização de drivers de vídeo ou sistema pode ser necessária. Recomenda-se verificar o site do fabricante."
            })

        # 5. Restart
        otimizacoes = payload.get("otimizacoes", {})
        if otimizacoes.get("sucessos", 0) > 0:
            recs.append({
                "codigo": "RESTART_REQUIRED",
                "nivel": "info",
                "titulo": "Reinício Recomendado",
                "descricao": "Reinicie o computador para garantir que todas as otimizações aplicadas entrem em vigor corretamente."
            })

        # 6. No Action
        if not recs:
            recs.append({
                "codigo": "NO_ACTION",
                "nivel": "sucesso",
                "titulo": "Sistema em Ótimas Condições",
                "descricao": "Nenhuma ação adicional imediata é necessária no momento."
            })
            
        payload["recomendacoes"] = recs
