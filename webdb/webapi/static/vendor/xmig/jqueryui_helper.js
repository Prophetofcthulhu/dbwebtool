(function () {
    // see https://www.tutorialspoint.com/jqueryui/jqueryui_dialog.htm
    //     http://jquery.page2page.ru/index.php5/UI_%D0%BF%D0%BE%D0%B7%D0%B8%D1%86%D0%B8%D0%BE%D0%BD%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5
    'use strict';
     var ui_holder = null;

     window.$uihelper = {
         init: function (holder_root_id) {
             ui_holder = holder_root_id;
         }
     };

    window.$JQDialog = function() {
        this.holder_root_id = null;
        this.base_id_prefix = "WGT";
        this.id = null;
        this.selector = function () {
            return $$.as_id_selector(this.id)
        };
        this.get_holder = function() {
            return this.holder_root_id ? this.holder_root_id : ui_holder
        };
        this.set_holder = function(holder) {
            this.holder_root_id = ui_holder
        };
        this._destroy = function() {
        };

        this.compose_placeholder_for_id = function(id) {
            return '<div id="'+ id +'" style="display:none;"></div>'
        };
        this.create = function(title, height, width, content, before_close, on_close) {
            this.id = $$.unique_id(this.base_id_prefix);
            var placeholder = this.compose_placeholder_for_id(this.id);

            $($$.as_id_selector(this.get_holder())).append(placeholder);

            $(this.selector()).dialog({
                //position: { my: "center top", at: "center top", of: window, offset: "100 100" },
                position: { my: "center", at: "center", of: window, offset: "100 100" },
                height: height,
                width: width,
                title: title,
                resizable: true,
                draggable: true,
                dialogClass: "alertDialog",
                modal: true,
                close: on_close,
                beforeClose: before_close
            });
            if ($$.is_defined(content)) {
                $(this.selector()).html(content)
            }
            return this
        };

        this._close = function() {
            $(this.selector()).dialog("close")
        };
        this._destroy = function() {
            $(this.selector()).dialog("destroy")
        };
        this.get_wrapper = function() {
            return $(this.selector()).parent()
        };
        this.get_inner_dom_element = function (index) {
            return $(this.selector()).get(index || 0);
        };
        this.hide = function() {
            $(this.selector()).dialog("widget").hide()
        };
        this.show = function() {
            $(this.selector()).dialog("widget").show()
        };
        this.open = function() {
            $(this.selector()).dialog("open")
        };
        this.set_position = function(x, y) {
            $(this.selector()).dialog("option", "position", [x, y]);
        };
        this.set_option_position = function(position) {
            $(this.selector()).dialog("option", "position", position);
        };
        this.set_size = function(x, y) {
            $(this.selector()).dialog({ width: x });
            $(this.selector()).dialog({ height: y });
        };
        this.get_width = function () {
            return $(this.selector()).dialog("option", "width");
        };
        this.get_height = function () {
            return $(this.selector()).dialog("option", "height");
        };
        this.increase_size = function(x, y) {
            this.set_size(x + this.get_width(), y + this.get_height());
        };
    };

})();

