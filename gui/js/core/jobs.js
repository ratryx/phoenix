(function (Phoenix) {
    "use strict";

    Phoenix.jobs.awaitJob = function (jobId, progressCallback) {
        return new Promise(function (resolve, reject) {
            var MAX_TENTATIVAS = 120; // 60 segundos máximo (120 × 500ms)
            var tentativas = 0;

            function check() {
                tentativas++;
                if (tentativas > MAX_TENTATIVAS) {
                    reject(new Error("Timeout: job demorou mais de 60s"));
                    return;
                }
                
                Phoenix.bridge.call("verificar_tarefa", jobId)
                    .then(function (estado) {
                        if (progressCallback && estado.progresso !== undefined) {
                            progressCallback(estado.progresso, estado.mensagem);
                        }
                        if (estado.status === "done") {
                            resolve(estado.resultado);
                        } else if (estado.status === "not_found") {
                            reject(new Error("Job não encontrado: " + jobId));
                        } else {
                            setTimeout(check, 500);
                        }
                    })
                    .catch(reject);
            }

            setTimeout(check, 500);
        });
    };

    // Global temporário para componentes não refatorados
    window.awaitJob = Phoenix.jobs.awaitJob;

})(window.Phoenix);
