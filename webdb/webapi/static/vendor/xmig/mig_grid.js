(function () {
    'use strict';

window.$grid = {
    set_css_var: function (var_name, var_value) {
        document.documentElement.style.setProperty(var_name, var_value);
    },
    get_css_var: function (var_name) {
        var styles = window.getComputedStyle($("html"));
        return styles.getPropertyValue(var_name)
    },
    set_table_columns: function (table_name, columns_number) {
        document.documentElement.style.setProperty("--colNum", columns_number);
    },
};

}());