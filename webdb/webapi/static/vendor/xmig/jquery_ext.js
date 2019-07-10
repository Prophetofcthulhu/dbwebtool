// Suppose using jQuery
//---------------------------------------------------------------------

$.fn.kill = function () {
    this.get()[0].outerHTML = "";
};


$.fn.disable = function () {
    return this.each(function () {
        if (typeof this.disabled !== "undefined") { this.disabled = true; }
    });
};

$.fn.enable = function (val) {
    return this.each(function () {
        if (typeof this.disabled !== "undefined") { this.disabled = (val !== "yes"); }
    });
};

$.fn.is_visible = function () {
    return this.is(":visible")
};
