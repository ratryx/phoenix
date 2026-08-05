(function (Phoenix) {
    "use strict";

    Phoenix.jobs.awaitJob = function (jobId, arg2, arg3) {
        return new Promise(function (resolve, reject) {
            var progressCallback = null;
            var options = {};

            if (typeof arg2 === "function") {
                progressCallback = arg2;
                if (arg3 && typeof arg3 === "object") {
                    options = arg3;
                }
            } else if (arg2 && typeof arg2 === "object") {
                if (typeof arg2.progressCallback === "function") {
                    progressCallback = arg2.progressCallback;
                }
                options = arg2;
            }

            var signal = options.signal;
            var pollIntervalMs = options.pollIntervalMs;

            if (typeof pollIntervalMs !== "number" || isNaN(pollIntervalMs) || pollIntervalMs < 100) {
                pollIntervalMs = 500;
            }

            var timerId = null;
            var abortHandler = null;
            var settled = false;

            function cleanup() {
                if (timerId !== null) {
                    clearTimeout(timerId);
                    timerId = null;
                }
                if (signal && abortHandler) {
                    signal.removeEventListener("abort", abortHandler);
                    abortHandler = null;
                }
            }

            function resolveOnce(val) {
                if (settled) return;
                settled = true;
                cleanup();
                resolve(val);
            }

            function rejectOnce(err) {
                if (settled) return;
                settled = true;
                cleanup();
                reject(err);
            }

            var cancelRequested = false;

            if (signal) {
                if (signal.aborted) {
                    cancelRequested = true;
                    Phoenix.bridge.call("cancelar_tarefa", jobId).catch(function() {});
                }
                abortHandler = function () {
                    if (settled || cancelRequested) return;
                    cancelRequested = true;
                    Phoenix.bridge.call("cancelar_tarefa", jobId).catch(function() {});
                };
                signal.addEventListener("abort", abortHandler);
            }

            function check() {
                if (settled) return;
                
                Phoenix.bridge.call("verificar_tarefa", jobId)
                    .then(function (estado) {
                        if (settled) return; // Se abortou no meio da chamada in-flight
                        
                        if (progressCallback && estado.progresso !== undefined) {
                            progressCallback(estado.progresso, estado.mensagem, estado.detalhes_progresso);
                        }
                        
                        if (["done", "failed", "cancelled", "timed_out"].includes(estado.status)) {
                            resolveOnce(estado.resultado);
                        } else if (estado.status === "not_found") {
                            rejectOnce(new Error("Falha na consulta de status do processo interno."));
                        } else {
                            if (!settled) {
                                timerId = setTimeout(check, pollIntervalMs);
                            }
                        }
                    })
                    .catch(function (err) {
                        if (settled) return;
                        rejectOnce(err);
                    });
            }

            timerId = setTimeout(check, pollIntervalMs);
        });
    };

    // Global temporário para componentes não refatorados
    window.awaitJob = Phoenix.jobs.awaitJob;

})(window.Phoenix);
