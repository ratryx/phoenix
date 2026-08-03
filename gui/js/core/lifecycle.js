(function (Phoenix) {
    "use strict";

    const _timers = {};

    Phoenix.lifecycle.setInterval = function (name, callback, delay) {
        if (_timers[name]) {
            clearInterval(_timers[name]);
        }
        _timers[name] = setInterval(callback, delay);
        return _timers[name];
    };

    Phoenix.lifecycle.clearInterval = function (name) {
        if (_timers[name]) {
            clearInterval(_timers[name]);
            delete _timers[name];
        }
    };

    Phoenix.lifecycle.clearAll = function () {
        for (const name in _timers) {
            clearInterval(_timers[name]);
            delete _timers[name];
        }
    };

    Phoenix.lifecycle.leavePage = function (pageName) {
        // Obsoleto: substituído por chamadas genéricas no router
    };

})(window.Phoenix);
