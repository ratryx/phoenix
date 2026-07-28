(function (Phoenix) {
    "use strict";

    Phoenix.jobs.awaitJob = function (jobId, optionsOrCallback) {
        return new Promise(function (resolve, reject) {
            var progressCallback = null;
            var signal = null;

            if (typeof optionsOrCallback === "function") {
                progressCallback = optionsOrCallback;
            } else if (optionsOrCallback && typeof optionsOrCallback === "object") {
                progressCallback = optionsOrCallback.progressCallback;
                signal = optionsOrCallback.signal;
            }

            var timerId = null;

            function cleanup() {
                if (timerId !== null) {
                    clearTimeout(timerId);
                    timerId = null;
                }
            }

            if (signal) {
                if (signal.aborted) {
                    Phoenix.bridge.call("cancelar_tarefa", jobId);
                    reject(new Error("Job cancelado localmente."));
                    return;
                }
                signal.addEventListener("abort", function () {
                    cleanup();
                    Phoenix.bridge.call("cancelar_tarefa", jobId);
                    reject(new Error("Job cancelado localmente."));
                });
            }

            function check() {
                Phoenix.bridge.call("verificar_tarefa", jobId)
                    .then(function (estado) {
                        if (progressCallback && estado.progresso !== undefined) {
                            progressCallback(estado.progresso, estado.mensagem);
                        }
                        if (["done", "failed", "cancelled", "timed_out"].includes(estado.status)) {
                            cleanup();
                            resolve(estado.resultado);
                        } else if (estado.status === "not_found") {
                            cleanup();
                            reject(new Error("Job não encontrado: " + jobId));
                        } else {
                            if (timerId !== null) {
                                timerId = setTimeout(check, 500);
                            }
                        }
                    })
                    .catch(function(err) {
                        cleanup();
                        reject(err);
                    });
            }

            timerId = setTimeout(check, 500);
        });
    };

    // Global temporário para componentes não refatorados
    window.awaitJob = Phoenix.jobs.awaitJob;

})(window.Phoenix);
