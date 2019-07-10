
window.performance = window.performance || {};
performance.now = (function() {
    return performance.now    ||
        performance.mozNow    ||
        performance.msNow     ||
        performance.oNow      ||
        performance.webkitNow ||
        Date.now  /*none found - fallback to browser default */
})();

function timemark() {
    var start = performance.now();
    return {
        delta: function () {
            return Math.round((performance.now() - start) * 100) / 100;
        }
    }
}
