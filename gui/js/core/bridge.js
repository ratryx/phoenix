(function (Phoenix) {
    "use strict";

    let _readyPromise = null;

    Phoenix.bridge.whenReady = function () {
        if (_readyPromise) {
            return _readyPromise;
        }

        if (window.pywebview && window.pywebview.api) {
            _readyPromise = Promise.resolve();
            return _readyPromise;
        }

        _readyPromise = new Promise(function (resolve) {
            window.addEventListener("pywebviewready", function onReady() {
                window.removeEventListener("pywebviewready", onReady);
                resolve();
            });
        });

        return _readyPromise;
    };

    Phoenix.bridge.isReady = function () {
        return !!(window.pywebview && window.pywebview.api);
    };

    Phoenix.bridge.call = async function (methodName, ...args) {
        await Phoenix.bridge.whenReady();
        
        const api = window.pywebview.api;
        if (typeof api[methodName] !== "function") {
            throw new Error("Método não encontrado na bridge Python: " + methodName);
        }

        return api[methodName].apply(api, args);
    };

})(window.Phoenix);
