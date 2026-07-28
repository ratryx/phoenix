(function (Phoenix) {
    "use strict";

    Phoenix.jobs.awaitJob = function (jobId, arg2, arg3) {
        return new Promise(function (resolve, reject) {
            var progressCallback = null;
            var signal = null;

            if (typeof arg2 === "function") {
                progressCallback = arg2;
                if (arg3 && typeof arg3 === "object") {
                    signal = arg3.signal;
                }
            } else if (arg2 && typeof arg2 === "object") {
                progressCallback = arg2.progressCallback;
                signal = arg2.signal;
            }

            var timerId = null;
            var abortHandler = null;

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

            if (signal) {
                if (signal.aborted) {
                    Phoenix.bridge.call("cancelar_tarefa", jobId);
                    resolve({ ok: false, codigo: "JOB_CANCELLED", erro: "Operação cancelada pelo usuário." });
                    return;
                }
                abortHandler = function () {
                    cleanup();
                    Phoenix.bridge.call("cancelar_tarefa", jobId);
                    resolve({ ok: false, codigo: "JOB_CANCELLED", erro: "Operação cancelada pelo usuário." });
                };
                signal.addEventListener("abort", abortHandler);
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
                            reject(new Error("Falha na consulta de status do processo interno.")); // DO NOT leak job ID
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
