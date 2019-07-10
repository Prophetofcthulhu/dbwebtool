(function () {
    'use strict';

    window.$Card = function() {
        this.wname = "";
        this.template_name = "card_template";
        this.all_interesting_items = [];
        this.current_index = 0;
        this.window_id = null;
        this.config = {
            autoplay: false,
            autonext:  false,
            autonext_timeout: 1000,
            viewsettings: false
        };
        this.controls = {
            previous: false,
            next: false
        };
        this.init = function(wname, template_name) {
            this.wname = wname;
            if ($$.is_defined(template_name)) {
                this.template_name = template_name
            }
            this.all_interesting_items = [];
            this.current_index = 0;
            return this
        };
        this.on_render = function () {};
        this.on_close = function (card) {};
        this.fix_item = function (item) { return item };
        this.before_next = function () {};
        this.before_previous = function () {};

        this.set_param = function(name, value) {
            this.config[name] = value;
            if (name === 'autoplay' && !value && $$.is_defined(this._autonext_timeout)) {
                clearTimeout(this._autonext_timeout)
            }
        };

        this.set_control = function(name, value) {
            this.controls[name] = value;
        };
        this.get_control = function(name) {
            return this.controls[name];
        };
        this.get_param = function(name) {
            return $$.is_defined(this.config[name]) ? this.config[name] : false;
        };
        this._collect_interesting = function(uuid) {
            var self = this,
                index = 0;

            this.current_index = 0;
            $tablerender.iterate(this.wname, function (row, i) {
                self.all_interesting_items.push(i);
                if ($$.is_defined(uuid) && row.uuid === uuid) {
                    index = i
                }
            });
            for (var i=0; i<self.all_interesting_items.length; i+=1) {
                if (self.all_interesting_items[i] === index) {
                    self.current_index = i;
                    break
                }
            }
        };
        this._get_template = function(params) {
            params = $$.is_defined(params) ? params : {};
            var template = window.renderers[this.wname][this.template_name],
                autoplay = (this.config.autoplay && params['autoplay'] !== 'skip') ? "autoplay" : "";
            return $sound.audio_expand(template, this.context.sound_prefix, autoplay)
        };
        this._update_widget = function() {
            //params = $$.is_defined(params) ? params : {};
            var key;
            for (key in this.config) {
                if ($$.as_bool(this.config[key])) {
                    $($$.as_id_selector("ctl_" + key + this.wname)).prop("checked", true);
                    $($$.as_class_selector("impl_" + key + this.wname)).show();
                }
            }
            for (key in this.controls) {
                if (! $$.as_bool(this.controls[key])) {
                    $($$.as_id_selector("do_" + key + this.wname)).prop("disabled", true);
                }
            }
        };

        this._compose_card_content = function(params) {
            var row = $tablerender.item_by_index(this.wname, this.all_interesting_items[this.current_index]),
                template = this._get_template(params),
                context = this.context,
                config = this.config;
                row = this.fix_item(row);
                return _.template(template)({data: row, uuid: row.uuid, sound: row.sound, CONTEXT: context, CONFIG: config});
        };
        this.get_item = function () {
            return $tablerender.item_by_index(this.wname, this.all_interesting_items[this.current_index]);
        };
        this.set_item = function(param_name, value, need_render) {
            var row = this.get_item();
            row[param_name] = value;
            if ($$.is_defined(need_render) && need_render) {
                $tablerender.render(this.wname);
            }
        };
        this.get_item_param = function(param_name) {
            var row = this.get_item();
            return row[param_name];
        };
        this.get_current_index = function() {
            return this.current_index;
        };
        this.get_max_current_index = function() {
            return this.all_interesting_items.length;
        };
        this.get_item_by_index = function(idx) {
            return this.all_interesting_items[idx];
        };
        this.parent_render = function() {
            $tablerender.render(this.wname);
        };
        this.toggle_item = function(param_name, need_render_card, need_render_table) {
            need_render_card  = $$.is_defined(need_render_card)  ? need_render_card : true;
            need_render_table = $$.is_defined(need_render_table) ? need_render_table: true;
            var row = $tablerender.item_by_index(this.wname, this.all_interesting_items[this.current_index]);
            row[param_name] = ! ($$.is_defined(row[param_name]) && row[param_name]);

            if (need_render_table) {
                $tablerender.render(this.wname);
            }

            if (need_render_card) {
                this.render({autoplay: 'skip'})
            }
        };
        this.toggle_param = function(param_name, need_render) {
            var new_value = ! this.get_param(param_name);
            this.set_param(param_name, new_value);
            if ($$.is_defined(need_render) && need_render) {
                var skip = param_name === 'autoplay' ? null : {autoplay: 'skip'};
                this.render(skip);
            }
            return new_value
        };

        this.render = function(params) {
            var self = this,
                timeout = this.get_param("autonext_timeout");

            $($$.as_id_selector(this.window_id)).html(this._compose_card_content(params));

            this.set_control("previous", this.current_index > 0);
            this.set_control("next", this.current_index < this.all_interesting_items.length -1);

            if (! this.get_control("next")) {
                this.set_param("autonext", false);
                if ($$.is_defined(this._autonext_timeout)) {
                    clearTimeout(this._autonext_timeout)
                }
            }

            this._update_widget();
            this.on_render(this);

            if (this.get_param("autonext")) {
                this._autonext_timeout = setTimeout(function () {
                    self.next_card_item();
                }, timeout)
            }
        };
        this.destroy = function() {
            $($$.as_id_selector(this.window_id)).html("");
            this._destroy();
        };
        this.close = function() {
            $($$.as_id_selector(this.window_id)).html("");
            this._close();
        };
        this.card_item_render = function(pre_process_fn) {
            if (pre_process_fn) {
                pre_process_fn()
            }
            this.render();
        };
        this.previous_card_item = function() {
            this.current_index =  Math.max(0, this.current_index - 1);
            this.before_previous();
            this.card_item_render()
        };

        this.next_card_item = function() {
            this.current_index += 1;
            this.before_next();
            this.card_item_render()
        };
        this.make_panel = function(wname, template_name, hight, weight, config, uuid, skip_render) {
            var self = this;

            this.init(wname, template_name);
            this._collect_interesting(uuid);
            //title, height, width, content, before_close, on_close
            this.window_id = this.create("", hight, weight, "", function () {self.on_close(self)}, function() {self.destroy()}).id;
            if ($$.is_defined(config)) {
                this.config = Object.assign(this.config, config)
            }
            if (! $$.is_defined(skip_render) || ! skip_render) {
                this.render();
            }

            return this;
        }
        
    };
    $Card.prototype = new $JQDialog();
})();