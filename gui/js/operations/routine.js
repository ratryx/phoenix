(function (Phoenix) {
    "use strict";

    const bridge = Phoenix.bridge;
    const jobs = Phoenix.jobs;
    const feedback = Phoenix.ui.feedback;
    const router = Phoenix.router;

    const operation = {};
    let executando = false;

    operation.execute = async function () {
        if (executando) return;
        executando = true;

        try {
            await Phoenix.operations.restorePoint.runProtected(async function () {
                feedback.mostrarOverlay(
                    "Executando rotina completa — isso pode levar alguns minutos...", true
                );
                try {
                    var jobRes = await bridge.call("executar_rotina_completa", "");
                    if (!jobRes || !jobRes.job_id) {
                        return;
                    }
                    
                    var resultado = await jobs.awaitJob(jobRes.job_id);

                    if (!resultado || !resultado.ok) {
                        await feedback.confirmarModal(
                            'Erro na Rotina',
                            "Erro ao executar rotina completa: " + (resultado && resultado.erro || "Erro desconhecido"),
                            '🚨'
                        );
                        return;
                    }

                    router.navigate("relatorio");
                    Phoenix.pages.relatorio.showResult(resultado);
                } catch (e) {
                    console.error("[ERRO] Rotina completa:", e);
                    if (e.message !== "Job cancelado localmente.") {
                        await feedback.confirmarModal(
                            'Erro',
                            'Ocorreu um erro ao processar a rotina.',
                            '🚨'
                        );
                    }
                } finally {
                    feedback.esconderOverlay(true);
                }
            });
        } finally {
            executando = false;
        }
    };

    Phoenix.operations = Phoenix.operations || {};
    Phoenix.operations.routine = operation;

})(window.Phoenix);
