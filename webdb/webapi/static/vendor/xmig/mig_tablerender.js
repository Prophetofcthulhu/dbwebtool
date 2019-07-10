(function () {
    'use strict';
    var version = "1.0.1";
    var icon = {
        "sort": "fa-sort",
        "down": "fa-sort-down",
        "up":   "fa-sort-up",
    };

    window.$tablerender = {
        views: {},
        system_fields: ["SYS", "CONTEXT", "data"],
        default_kind: null,
        default_config: {
                    name: "",
                    base: null,
                    url: "",
                    verbose: false,
                    view_mode_default: "view_template",
                    view_mode: "",
                    view_title_mode: "skipped",
                    current_columns_number: 0,
                    template: "",
                    templates: [],
                    target_data: "",
                    target_title: "",
                    max_id: -1,
                    current_next_id: -1,
                    current_active_first_index: 0,  // index of the first (paged) row
                    search_fields: [],
                    context: {},
                    search_mode: "anySubstring", // anySubstring || startsWith
                    search_query_id: "search_query_id",
                    filter_action_default: "eq",
                    filter_case_sensitive: false,
                    search_case_sensitive: false,
                    data: null,
                    data_types: {},
                    empty_record: [],
                    datapoint: null,
                    items: [],
                    page: 0,
                    page_size: 100,
                    auto_audio: false,
                    filters: [],
                    sorters: [],
                    sort_dirs: {},
                    after_upudaters: {},
                    applied_sort_elements: {},
                    random_sort: false,
                    sys: {
                        last_action: null
                    },
                    injected_functions: {},
                    events: {
                        postload: [],
                        on_render: function (view) {},
                        on_clone: function (item, action, base_item) {}
                    }
                    //filters: ['important']
                    //filters: [{key: 'important', value: true}]
        },
        kind: function(name) {
            return $$.is_defined(name) ? name : this.default_kind
        },
        set_def_kind: function(name) {
            if ($$.is_defined(name)) {
                this.default_kind = name;
            }
            else {
                console.log("Skipped set_def_kind as empty")
            }
        },
        item_by_index: function(name, index) {
            name = $tablerender.kind(name);
            return this.views[name].data[index]
        },
        add_view: function(config, name) {
            var self = this;
            name = name || config.name || config.kind;
            this.views[name] = config;

            Object.keys(self.default_config).forEach(function(key) {
                if (! $$.is_defined(config[key])) {
                    config[key] = self.default_config[key]
                }
            });
            //console.log("CONFIG:", this.views[config.name])
        },
        view_by_name: function(name) {
            return this.views[name]
        },
        // get_template: function(name, template_name) {
        //     var view = this.views[name];
        //     return view.templates[template_name]
        // },
        set_view_mode: function(name, mode) {
            var view = this.views[name];
            view.view_mode = mode
        },
        _collect_max_id: function(name) {
            var self = this,
                view = this.views[name];
            this.row_iterator(name, function (row) {
                if ($$.is_defined(row["_id_"])) {
                    view.max_id = Math.max(view.max_id, row["_id_"])
                }
            });
            view.current_next_id = view.max_id + 1;
        },
        create_next_id: function(name) {
            var self = this,
                view = this.views[name];
                if (view.max_id !== -1) {
                    view.current_next_id += 1;
                    console.log("NEXT ID", view.current_next_id, "MAX ID:", view.max_id);
                    return view.current_next_id;
                }
                else {
                    return $$.unique_id()
                }
        },
        // apply_templates: function(name) {
        //     var view = this.views[name],
        //         meta = $$.is_defined(view.addinfo) ? view.addinfo.meta : {menu_template: null},
        //         menu = meta.menu_template ? $$.is_defined(meta.menu_template) : "",
        //         menu_html = menu ? view.templates[menu] : "";
        //
        //     $("#additional_menu_id").html(menu_html);
        //     view.view_mode = $$.is_defined(meta.item_template) ? meta.item_template : view.view_mode_default;
        //
        //     // console.log("VIEW MODE. Meta:", meta, view.view_mode);
        //     // console.log("ADDITIONAL MENU", menu, menu_html);
        // },


        _after_loading:  function(name, apply_dynamic_templates) {
            var self = this,
                view = this.views[name];
                self._collect_max_id(name);
                if ($$.is_array(view.events.postload)) {
                    view.events.postload.forEach(function (method) {
                        if ($$.is_function(method)) {
                            method(name)
                        }
                    });
                }
                self._render(name, apply_dynamic_templates)
        },
        render: function(name, data) {
            var self = this,
                view = this.views[name];

            var apply_dynamic_templates = function(name) {
                name = $tablerender.kind(name);
                var view = $tablerender.views[name];
                $$.object_keys(view.templates).forEach(function (key) {
                    if ($$.last_chars(key, 3) === "_id") {
                        document.getElementById($$.as_plain_id(key)).innerHTML = view.templates[key]
                    }
                })
            };

            var render_success = function(view_name) {
                // console.log("Render  [" + view_name + "] ...");
                self._after_loading(view_name, apply_dynamic_templates);
            };

            if (! $$.is_defined(view) || ! view.data) {
                // console.log("LOADDDDDDD!!!")
                if (! $$.is_defined(data)) {
                    return this.load(name, {}, render_success)
                }
            }
            else {
                 // console.log("SKIP LOADDDDDDDING!")
                self.data_update(name, data);
            }
            return self._render(name, apply_dynamic_templates);
        },
        toggle_filter_for: function(name, filter_key, row_value, row_key) {
            var key = $$.is_defined(row_key) ? row_key : "uuid";

            this.row_iterator(name, function(row, i) {
                if (row[key] === row_value) {
                    if ($$.is_defined(row[filter_key]) && row[filter_key]) {
                        row[filter_key] = false;
                    }
                    else {
                        row[filter_key] = true;
                    }
                    return true
                }
            }, "first_case_break");
            this._render(name);
        },
        _add_filter: function(name, filter) {
            var self = this,
                view = this.views[name],
                filters = view.filters;

            if (filter.titleref) {
                $(filter.titleref).html(filter.title);
            }
            filters.push(filter);
        },
        add_filter: function(name, filter, skip_render) {
            this._add_filter(name, filter);
            if (! $$.is_true(skip_render)) {
                this._render(name)
            }
            return 1;
        },
        filter_iterator: function(name, callback, mode) {
            var view = this.views[name],
                successes = 0,
                filters = view.filters,
                count_of_filters = filters.length;

            for (var i=0; i<filters.length; i+=1) {
                var filter = filters[i],
                    key = filter,
                    value = true;

                if ($$.is_object(filter)) {
                    key = filter["key"];
                    value = filter["value"];
                }

                if (callback(key, value, filter)) {
                    if (mode === "first_case_break") {
                        return true
                    }
                    successes += 1
                }
            }
            return successes === count_of_filters
        },
        remove_filter_group: function(name, filter, skip_render) {
            var self = this,
                view = this.views[name],
                group = $$.is_object(filter) ? filter["group"] : filter,
                temp = [];

            self.filter_iterator(name, function(key, value, filter) {
                    if (filter.group !== group) {
                        temp.push(filter);
                    }
                });

            view.filters = temp;

            if ($$.is_defined(skip_render)) {
                return
            }
            this._render(name);
        },
        _remove_filter: function(name, filter) {
            var self = this,
                view = this.views[name],
                qkey = $$.is_object(filter) ? filter["key"] : filter,
                temp = [];
            //console.log("Removing .... [" + qkey + "]")
            self.filter_iterator(name, function(key, value, filter) {
                    if (key !== qkey) {
                        temp.push(filter);
                    }
                });
            if (filter.titleref) {
                $(filter.titleref).html("");
            }
            view.filters = temp;
        },
        _remove_all_auto_filters: function (name, filter_mode) {
            var view = this.views[name],
                temp = [];

            this.filter_iterator(name, function(key, value, filter) {
                    if (filter._filter_mode_ !== filter_mode) {
                        temp.push(filter);
                    }
                });
            view.filters = temp;
        },

        remove_filter: function(name, filter) {
            this._remove_filter(name, filter);
            this._render(name);
            return 0;
        },
        has_some_filter: function(name) {
            return this.views[name].filters.length > 0
        },

        is_already_applied_filter: function (name, filter_key) {
            if (! this.has_some_filter(name)) {
                return false
            }
            return this.filter_iterator(name, function(key, value, filter) {
                return filter_key === key;
            }, "first_case_break");
        },
        toggle_filter: function(name, filter, value) {
            var key = $$.is_object(filter) ? filter["key"] : filter;
            if (this.is_already_applied_filter(name, key)) {
                return this.remove_filter(name, filter)
            }
            else {
                return this.add_filter(name, filter)
            }
        },
        swap_filter: function(element, name, new_action) {
            var filter_str = jQuery.find.attr(element, "filter"),
                filter = JSON.parse(filter_str),
                key = $$.is_object(filter) ? filter.key : filter;

            //console.log("SWAP FILTER 0: key: ["  + key + "]", filter)

            if ($$.is_defined(new_action)) {
                filter.action = new_action
            }

            //console.log("SWAP FILTER 1: key: ["  + key + "]", filter)

            if (this.is_already_applied_filter(name, key)) {
                //console.log("REMOVE FILTER : key: ["  + key + "]")
                this.remove_filter(name, filter)
            }
            else {
                //console.log("REMOVE FILTER : key: ["  + key + "]", filter)
                this.add_filter(name, filter)
            }
            // render already applied here - with 'remove_filter' or 'add_filter'
        },
        next_filter: function(element, name) {
            var filter_str = jQuery.find.attr(element, "filter"),
                filter = JSON.parse(filter_str),
                key = $$.is_object(filter) ? filter["key"] : filter,
                filter_value = $$.is_object(filter) ? filter["value"] : null;

            if (filter_value === "*" || this.is_already_applied_filter(name, key)) {
                if (filter.nextfilter) {

                    $(element).hide();
                    $(filter.nextfilter).show();
                    this._remove_filter(name, filter);

                    if (filter_value !== "*") {
                        $(filter.nextfilter).click();   // apply & render
                    }
                }
            }
            else {
                this._add_filter(name, filter)
            }
            this._render(name)
        },
        _filter_action_default: function(value, default_action) {
            return $$.is_string(value) ? "startsWith" : default_action
        },
        //FILTER anySubstring true true boolean
        filter_ok: function(name, row) {
            var self = this,
                view = this.views[name],
                verbose = view.verbose,
                search_filters_count = 0,
                search_ok = 0,
                filter_performer = function(action) {
                    var actions = {
                        startsWith   : function(value, qvalue) {
                            return $$.is_string(value) ? value.startsWith(qvalue) : value === qvalue },
                        anySubstring : function(value, qvalue) {
                            return $$.is_string(value) ? value.indexOf(qvalue) !== -1 : value === qvalue },
                        greater      : function(value, qvalue) { return value < qvalue},
                        less         : function(value, qvalue) { return value > qvalue},
                        eq           : function(value, qvalue) { return value === qvalue}
                    };
                    return actions[action]
                },
                value_extractor = function(key) {
                    var value = $$.get_dotted_value(key, row);
                    if (value) {
                        // wrong data structure fix
                        if (Array.isArray(value)) {
                            value = value[0]
                        }
                    }
                    return value
                };

            this.filter_iterator(name, function(filter_key, filter_value, filter) {
                var accessor = filter.field ? filter.field : filter_key,
                    value = filter.value ? filter.value : filter_value;

                    var real_value = value_extractor(accessor),
                        action = filter._filter_action_
                            || filter.action
                            || self._filter_action_default(real_value, view.filter_action_default);

                    if (! real_value) {
                        return false
                    }

                if (! view.search_case_sensitive) {
                    real_value = $$.to_lower(real_value);
                }

                if (filter._filter_mode_ === "search") {
                    search_filters_count += 1;
                    //console.log("FILTER[" + action + "] [" + value + "] [" + real_value + "]");
                    search_ok += filter_performer(action)(real_value, value) ? 1 : 0
                }
            }, "first_case_break");

            return ! (search_ok > 0 || search_filters_count === 0)
                ? false
                : this.filter_iterator(name, function(filter_key, filter_value, filter) {
                    var accessor = filter.field ? filter.field : filter_key,
                        value = filter.value ? filter.value : filter_value;

                    //console.log("FILTER", filter)

                    if (filter._filter_mode_ === "search") {
                        return true;    // already took into account
                    }
                    var real_value = value_extractor(accessor),
                        action = filter._filter_action_ || filter.action || view.filter_action_default;

                    if (! real_value) {
                        return false
                    }
                    //console.log("FILTER B [" + real_value + "]", filter);
                    return value ? filter_performer(action)(real_value, value)
                                 : false
                });
        },
        print_filters: function(name) {
            var view = this.views[name];
            console.log("***************************************");
            this.filter_iterator(name, function(filter_key, filter_value, filter) {
                console.log("FILTER: [" + filter_key + "] <" + filter_value + ">", filter)
            })
        },
        _apply_sort_direction_icon: function (e, direction) {
            e.removeClass(icon.sort).removeClass(icon.up).removeClass(icon.down);
            e.addClass(icon[direction]);
        },
        _get_sort_direction: function (name, e) {
            var view = this.views[name],
                sort_dirs = view.sort_dirs,
                direction = sort_dirs[e];

            if (! $$.is_defined(direction)) {
                direction = "up"
            }
            else {
                direction = direction === "up" ? "down" : "up"
            }
            sort_dirs[e] = direction;
            return direction;

            // if (e.hasClass(icon.SORT_UP)) {
            //     console.log("SORT_UP", e)
            //     e.removeClass(icon.SORT_UP).addClass(icon.SORT_DOWN);
            //     return "down";
            // }
            // // if (e.hasClass(icon.SORT_DOWN)) {
            // if (e.hasClass(icon.SORT_DOWN)) {
            //     console.log("SORT_DOWN", e)
            //     e.removeClass(icon.SORT_DOWN).addClass(icon.SORT_UP);
            //     return "up";
            // }
            // console.log("SORT_DEFAULT", e)
            // e.removeClass(icon.SORT).addClass(icon.SORT_UP);
            // return "up"
        },
        sort_random: function(name) {
             var self = this,
                view = this.views[name];
             view.random_sort = true;
             var compare = function(a, b) {
                return Math.floor(Math.random() * 10) > 4 ? 1 : -1
            };
             view.data.sort(compare);
             this._render(name)
        },
        sort_by: function(name, sorter, el) {
            var self = this,
                view = this.views[name],
                key = $$.is_object(sorter) ? sorter["key"] : sorter,
                e = $(el),
                this_id = e.prop("id"),
                sort_direction = this._get_sort_direction(name, e),
                xx = this._apply_sort_direction_icon(e, sort_direction),
                ab = sort_direction === "down" ? 1 : -1,
                ba = sort_direction === "down" ? -1 : 1;

            // console.log("SORT BY: [" + key + "] direction: [" + sort_direction + "] [" + this_id  + "] el=", el);
            view.applied_sort_elements[this_id] = el;
            $.map(view.applied_sort_elements, function (v, key) {
                if (key !== this_id) {
                    $(v).removeClass(icon.SORT_DOWN).removeClass(icon.SORT_UP).addClass(icon.SORT);
                }
            });

            var compare = function(a, b) {
                if (a[key] < b[key]) return ab;
                if (a[key] > b[key]) return ba;
                return 0;
            };

            view.data.sort(compare);
            self._render(name)
        },
        apply_sort: function(name) {
            name = this.kind(name);
            // console.log("APPLY SORT [" + name + "]");
            var self = this,
                view = this.views[name],
                sorters = view.sorters;

            if ($$.is_array(sorters) && sorters.length > 0) {
                var sorter = sorters[0],     // for now only a single sorter are applied
                    sort_direction = sorter.direction,
                    key = sorter.key,
                    ab = sort_direction === "down" ? 1 : -1,
                    ba = sort_direction === "down" ? -1 : 1;

                //console.log("SORT BY: [" + key + "] direction: [" + sort_direction + "] [" + button_id + "]");

                var compare_simple = function(a, b) {
                    if (a[key] < b[key]) return ab;
                    if (a[key] > b[key]) return ba;
                    return 0;
                },
                compare_dotted = function(a, b) {
                    if ($$.get_dotted_value(key, a) < $$.get_dotted_value(key, b)) return ab;
                    if ($$.get_dotted_value(key, a) > $$.get_dotted_value(key, b)) return ba;
                    return 0;
                };

                view.data.sort(key.indexOf(".") === -1 ? compare_simple : compare_dotted);
                self._render(name)
            }
        },

        row_iterator: function(name, callback, mode) {
            name = this.kind(name);
            // console.log("******* NAME: [" + name + "]", this.views[name]);
            var view = this.views[name],
                rows = view.data,
                count_of_rows = $$.is_defined(rows) ? rows.length : 0;

            for (var i=0; i<count_of_rows; i+=1) {
                if (callback(rows[i], i)) {
                    if (mode === "first_case_break") {
                        return true
                    }
                }
            }
        },
        _record_by_uuid: function(name, uuid) {
            var result = null,
                index = -1;
            this.row_iterator(name, function (row, i) {
            if ($$.is_defined(row.uuid) && row.uuid === uuid) {
                result = row;
                index = i;
                return true
            }
            return false
            }, "first_case_break");
            //return result
            return {item: result, index: index}
        },
        _remove_record: function(name, uuid, deleted_flag) {
            var row = this._record_by_uuid(name, uuid);
            if (row && row.item) {
                row.item._deleted_ = deleted_flag;
            }
        },
        remove_record: function(name, uuid) {
            this._remove_record(name, uuid, true);
            this._render(name);
            this.xupdate(name)
        },
        restore_record: function(name, uuid) {
            this._remove_record(name, uuid, false);
            this._render(name);
            this.xupdate(name)
        },

        _iterate: function(name, callback, need_page_info_update, condition) {
            name = this.kind(name);
            condition = $$.is_function(condition) ? condition : function (item) {return true};
            var self = this,
                view = this.views[name],
                index_shift = $$.is_defined(view.index_shift) ? view.index_shift : 0,
                max_index = $$.is_defined(view.data) ? view.data.length : 0,
                page_info_update = $$.is_true(need_page_info_update),
                page_size = view.page_size,
                count_pages,
                start_index,
                selecter_idx = [],
                selected_len,
                row,
                res = [];

            for (var index=index_shift; index<max_index; index+=1) {
                row = view.data[index];
                if (! condition(row)) {
                    continue
                }

                if (! row) {
                    break;
                }
                if (row._deleted_) {
                    continue
                }
                if (self.filter_ok(name, row)) {
                    selecter_idx.push(index);
                }
            }

            selected_len = selecter_idx.length;
            start_index = Math.max(0, view.page * page_size);

            if (view.current_active_first_index > 0 && view.sys.last_action === "PAGE_RESIZE") {
                view.sys.last_action = "";
                start_index = view.current_active_first_index;
                view.page = Math.ceil(start_index / view.page_size);
            }

            count_pages = Math.ceil(selected_len / page_size);
            if (view.page >= count_pages) {
                view.page = count_pages -1
            }
            if (start_index >= selected_len) {
                start_index = Math.max(0, start_index - page_size)
            }
            view.current_active_first_index = start_index;

            // console.log("INDEXES [" + selected_len + "] page [" + view.page + "]", selecter_idx);
            // console.log("start_index", start_index);

            if (view.page === -1) {
                view.page = 0;
                res.push(callback(view.empty_record, 0, {
                        page: 0,
                        pages: 0,
                        count: 0,
                        first: true,
                        last: true,
                        empty: true
                    }))
            }
            else {
                for (var i = start_index, cnt = page_size; i < selected_len && cnt > 0; i += 1, cnt -= 1) {
                    index = selecter_idx[i];
                    row = view.data[index];
                    res.push(callback(row, index, {
                        page: view.page,
                        pages: count_pages,
                        count: i,
                        first: i === 0,
                        last: i === selected_len - 1
                    }))
                }
                if (page_info_update) {
                    view.page_info = {page: view.page + 1, pages: count_pages};
                }
            }
            view.index_shift = 0;
            return res
        },

        iterate: function(name, callback) {
            return this._iterate(name, callback, true)
        },
        on_render: function (name, success) {
            name = this.kind(name);
            var view = this.views[name],
                events = view.events;
            events.on_render = success;
        },
        _render_data: function(name, postprocessor, need_page_info_update, condition) {
            name = this.kind(name);
            var view = this.views[name],
                page_size = view.page_size,
                addinfo = view.addinfo,
                previous_data = {SYS: {}, data: {}, CONTEXT: {}, old: {}},
                perform = $$.is_function(postprocessor) ? postprocessor : function(row) {return row};

            return this._iterate(name, function(row, index, context) {
                var current_index = context.count  +1,
                    page_index = current_index % page_size;

                var data = {
                    SYS: {
                        "kind": name,
                        "idx": current_index,
                        "index": page_index,
                        "even": current_index % 2 === 0,
                        "odd": current_index % 2 !== 0,
                        "empty": context.empty,
                        "first": context.first,
                        "last": context.last,
                        "inner": !(context.last || context.first),
                        "pagesize": page_size,
                        "page": context.page,
                        "pages": context.pages
                    },
                    CONTEXT: view.context,
                    data: row,
                    addinfo: addinfo,
                    old: previous_data
                };
                previous_data = data;
                return perform(data)

            }, need_page_info_update, condition);
        },

        _apply_template: function(template, item, localisation, static_data) {
            item = $$.is_defined(item) ? item : {};
            item.t = localisation;
            item.static = static_data;
            var template_processor = $$.is_function(template) ? template : _.template(template);
            // console.log("TEMPLATE", template_processor)
            // console.log("ITEM", item)
            return template_processor(item);
        },
        _apply_additional_templates: function(name, data) {
            data = $$.is_defined(data) ? data : {};
             var view = this.views[name],
                 static_data = view.static_data,
                 //localisation = $$.is_defined(view.translation) ? view.translation() : $i18.get_translation(),
                 localisation = $$.is_defined(view.translation) ? view.translation() : function (x) {return x},
                 templates = view.additional_templates || [];

             for (var i=0; i<templates.length; i+=1) {
                 var t = templates[i],
                     template = t.template,
                     target_data = t.target_data;
                 if (template && target_data) {
                     var doc = document.getElementById($$.as_plain_id(target_data));
                     if ($$.is_defined(doc)) {
                         doc.innerHTML = this._apply_template(template, data, localisation, static_data);
                     }
                 }
             }
        },
        empty_render: function(name) {
            this._apply_additional_templates(name)
        },
        _set_html: function(target, html) {
            document.getElementById($$.as_plain_id(target)).innerHTML = html;
            // document.getElementById($$.as_plain_id(target)).outerHTML = html;
            // var holder = $$.as_plain_id(target);
            // if ($$.is_defined(holder)) {
            //     document.getElementById(holder).outerHTML = html;
            // }
            // document.getElementById($$.as_plain_id(target)).outerHTML = html;
        },
        _render: function(name, success) {
            name = this.kind(name);
            var view = this.views[name],
                view_title_mode = view.view_title_mode,
                title_showed = view.title_displayed;

            // console.log("view_title_mode: [" + view_title_mode + "]");

            if (view_title_mode !== "skip" && ! $$.is_true(title_showed)) {
                view.title_displayed = true;
                this._render_title(name);
            }
            this._render_body(name, success);
        },
        _render_title: function(name, success) {
            name = this.kind(name);
            var self = this,
                view = this.views[name],
                target = view.target_title;

            if ($$.is_defined(target) && target !== '') {
                var title_data = view.title_data,
                    view_mode = view.view_mode,
                    static_data = view.static_data,
                    //localisation = $$.is_defined(view.translation) ? view.translation() : $i18.get_translation(),
                    localisation = $$.is_defined(view.translation) ? view.translation() : function (x) {return x},
                    template = view.templates.list_title,
                    injected_functions = view.injected_functions,
                    template_processor = $$.is_function(template) ? template : _.template(template),
                    title_data_expanded = $$.update_object(title_data, injected_functions),
                    html = self._apply_template(template_processor, title_data_expanded, localisation, static_data);

                // console.log("TITLE-DATA", title_data_expanded);
                // console.log("TITLE-template", template);
                // console.log("TITLE-target ["+ target + "]");

                 this._set_html(target, html);

                if ($$.is_defined(success)) {
                    success(name)
                }
            }
        },

        _render_body: function(name, success) {
            name = this.kind(name);
            var self = this,
                view = this.views[name],
                view_mode = view.view_mode,
                static_data = view.static_data,
                localisation = $$.is_defined(view.translation) ? view.translation() : function (x) {return x},
                template = $$.is_defined(view.templates[view_mode])
                    ? view.templates[view_mode] : $$.is_defined(view.templates.list_view)
                        ? view.templates.list_view : view.template,
                target = $$.is_string(view.target_data) ? view.target_data : view.target,
                injected_functions = view.injected_functions,
                template_processor = $$.is_function(template) ? template : _.template(template),
                html = this._render_data(name, function (item) {
                    $$.update_object(item, injected_functions);
                    return self._apply_template(template_processor, item, localisation, static_data);
                }, true) || [];
            // console.log("TARGET: [" + target + "]", html);
            this._set_html(target, html.join(""));

            //console.log("TIME1", tm.delta());
            if (view.auto_audio) {
                $sound.render_after_loading($$.as_id_selector(target));
            }

            this.set_handlers();
            self._apply_additional_templates(name);
            if ($$.is_defined (view.events.on_render)) {
                view.events.on_render(view);
            }

            if ($$.is_defined(success)) {
                success(name)
            }
            //console.log("TIME", tm.delta())
        },

        set_page_size: function(name, size) {
            name = this.kind(name);
            var view = this.views[name];
            view.page_size = parseInt(size, 10);
            view.sys.last_action = "PAGE_RESIZE";
            this._render(name);
        },
        previous_page: function(name) {
            name = this.kind(name);
            var view = this.views[name];
            view.page = Math.max(0, view.page - 1);
            this._render(name);
        },
        next_page: function(name) {
            name = this.kind(name);
            var view = this.views[name];
            var max_real_page = Math.floor(view.data.length / view.page_size);
            view.page = Math.min(max_real_page, view.page + 1);
            this._render(name)
        },
        home_page: function(name) {
            name = this.kind(name);
            var view = this.views[name];
            view.page = 0;
            this._render(name)
        },
        set_handlers: function() {
            $(".clickable").bind('click', function() {
                var value = $(this).text().trim();
                value = $$.first_word(value);
                if ($$.is_defined(window.opener)) {
                    window.opener.$trx.translate(value)
                }
                else {
                    console.log("PopUp")
                }
            });
        },
        present: function(value) {
            window.opener.$trx.translate(value)
        },

        _handle_search: function (name, qvalue) {
            var view = this.views[name];

            this._remove_all_auto_filters(name, "search");

            for (var i=0; i<view.search_fields.length; i+=1) {
               var field = view.search_fields[i].trim();
               //console.log("SEARCH: [" + field + "] [" + qvalue + "]");
               if (field) {
                    this._add_filter(name, {
                        key: field,
                        value: qvalue,
                        _filter_mode_: "search",
                        _filter_action_ : view.search_mode
                    })
               }
           }
           this._render(name);
        },
        handle_search: function (el, name) {
            name = this.kind(name);
            //console.log("HANDLE SEARCH: [" + name + "]")
            var view = this.views[name],
                case_sensitive = view.search_case_sensitive,
                qvalue = case_sensitive ? el.value : el.value.toLowerCase();

            this._handle_search(name, qvalue);
            return false;
        },
        reset_search: function (name, search_element_id) {
            name = this.kind(name);
            this._remove_all_auto_filters(name, "search");
            $($$.as_id_selector(search_element_id)).val("");
            this._render(name);
        },
        set_search_mode: function(el, name, mode, alternative_button_id) {
            var view = this.views[name],
                qvalue = $("#" + view.search_query_id).val();

            view.search_mode = mode;
            this._handle_search(name, qvalue);
            if ($$.is_defined(alternative_button_id)) {
                $(el).hide();
                $("#" + alternative_button_id).show();
            }
            return false;
        },
        rename_param: function(name, field_name, new_field_name) {
            this.row_iterator(name, function (row) {
                if ($$.is_defined(row[field_name])) {
                    row[new_field_name] = row[field_name]
                }
            })
        },
        fix_param: function(name, field_name, default_value) {
            this.row_iterator(name, function (row) {
                if (! $$.is_defined(row[field_name])) {
                    row[field_name] = $$.is_function(default_value) ? default_value(row[field_name]) : default_value;
                    //console.log("Fixed: [" + field_name + "] as [" + row[field_name] + "]", row)
                }
            })
        },
        inject_uuid: function(name) {
            //console.log("INJECT UUID [" + name + "]");
            return $tablerender.fix_param(name, 'uuid', function () {
                return $$.unique_id(name)
            })
        },
        inject_id: function(name, id_name) {
            id_name = $$.is_defined(id_name) ? id_name : '_id_';
            var index = -1;
            return $tablerender.fix_param(name, id_name, function () {
                index += 1;
                return index;
            })
        },
        find_param: function(name, field_name, value) {
            var result = null;
            this.row_iterator(name, function (row) {
                if ($$.is_defined(row[field_name]) && row[field_name] === value) {
                    result = row;
                    return true;
                }

            }, "first_case_break");
            return result;
        },
        load: function (name, request_data, success) {
           // console.log("LOAD");
           var self = this,
                request = request_data || {},
                view = this.views[name],
                url = view.url,
                url_mode = view.url_mode,
                ajax =  url_mode === "compressed" ? $ax.load_json_compressed : $ax.load_json;

           var tm = timemark();

           ajax(url, "GET", request, function (data) {
                var new_name = self.data_update(name, data);
                console.log("LOAD TIME: [" + tm.delta() + "] name: [" + new_name + "]");
                success(new_name)
           });
        },

        load_other: function(name, url) {
            var view = this.views[name];
            view.data = null;
            view.addinfo = [];
            view.url = url;
            view.filters = [];
            this.render(name, null)
        },
        add_after_upudater: function(name, key, method, param) {
            var view = this.views[name];
            view.after_upudaters[key] = {method: method, param: param};
            //console.log("ADDED",  view.after_upudaters)
        },
        del_after_upudater: function(name, key) {
            var view = this.views[name];
            delete view.after_upudaters[key];
            //console.log("REMOVED",  view.after_upudaters)
        },
        reload: function(name, completed_callback) {
            name = $tablerender.kind(name);
            var self = this,
                view = this.views[name];

            this.load(name, {}, function () {
                self._after_loading(name);
                self.apply_sort(name);

                $.map(view.after_upudaters, function (v, key) {
                    var method = v.method,
                        param = v.param;
                    if ($$.is_defined(method) && $$.is_function(method)) {
                        method(param)
                    }
                });
                if ($$.is_defined(completed_callback)) {
                    completed_callback()
                }

                $tablerender.set_def_kind(name);

                self._render(name);
            });
        },
        update: function (name, request_data, success) {
           var self = this,
                request = request_data || {},
                view = this.views[name],
                url = view.url;
            $ax.XLoadJson(url, "POST", request, function (data) {
                success(data)
            });
        },
        get_datapoint: function(view, datapointname) {
            return $$.is_defined(datapointname) ? datapointname : 'data';
        },
        compose_empty_line: function(view, data, addinfo) {
            var empty_data_line = {},
                empty_value = "",
                line = data[0];
            $$.object_keys(line).forEach(function (key) {
                 empty_data_line[key] = empty_value
            });
            view.empty_record = empty_data_line;
        },
        data_update: function(name, data, datapointname) {
            var view = this.views[name];

            if ($$.is_defined(data.meta)) {
                var model = data.meta.model,
                    types = data.meta.types;

                view.meta = data.meta;
            }

            if ($$.is_defined(data.view_model)) {
                view.view_model = data.view_model;
                this.update_view_model(name);
            }

            if ($$.is_defined(view) && data) {
                datapointname = this.get_datapoint(view, datapointname);
                view.data = data[datapointname];
                view.addinfo = data.addinfo;

                // console.log("DATAPOINT: [" + datapointname + "] DATA:", view.data);

                this.compose_empty_line(view, view.data, view.addinfo);
                if (data.tasks) {
                }
            }
            return name
        },

        extend_data: function(name, data, datapointname) {
            datapointname = this.get_datapoint(view, datapointname);
            var view = this.views[name];
            if ($$.is_defined(view) && data) {
                data.forEach(function (item) {
                    view.data.push(item)
                })
            }
        },
        remove_item: function(name, uuid, need_to_render) {
            var view = this.views[name],
                base = this._record_by_uuid(name, uuid),
                idx  = base.index,
                item  = base.item;

            view.data.splice(idx, 1);
            //console.log("Item [" + uuid + "] [" + idx + "] REMOVED");

            if ($$.is_defined(need_to_render) && need_to_render) {
                this._render(name);
            }
            return item;
        },
        new_record: function(name, base_uuid, model, need_to_render) {
            var self = this,
                view = this.views[name],
                base = $$.is_defined(base_uuid) ? this._record_by_uuid(name, base_uuid) : null,
                base_obj = base ? base.item : view.data[0],
                base_idx = base ? base.index : 0,
                action   = base ? "clone" : "new",
                uuid = $$.unique_id("new_"),
                system_fields = this.system_fields;

            //console.log("NEW BASE :[" + base_uuid + "] action: [" + action + "] OBJ:", base_obj);
            var obj  = {};
            $$.clone_object(obj, base_obj, model, system_fields);
            //console.log("NEW OBJ 0", obj);

            obj.uuid = uuid;
            obj._new_ = "yes";
            obj._id_ = this.create_next_id(name);

            view.data.splice(base_idx, 0, obj); // insert just after cloned Object or in begin
            view.events.on_clone(obj, action, base_obj);
            if ($$.is_defined(need_to_render) && need_to_render) {
                this._render(name);
            }

            return obj;
        },
        on_clone: function (name, success) {
            var view = this.views[name],
                events = view.events;
            events.on_clone = success;
        },
        xupdate: function (name) {
            console.log("UPDATE: [" + name + "]");
            this.update(name, {a: 100}, function(resulted_data) {});
        },
        register_renderer: function(name, config) {
            if(! $$.is_defined(window.renderer_)) {
                window.renderer_ = {}
            }
            window.renderer_[name] = { config: config };
            $tablerender.add_view(config);
        },
        start_external: function(name, action_name, key_name) {
            var self = this,
                view = this.views[name],
                actions = view.actions || {},
                action = actions[action_name];

            if (!action) {
                console.log("External Action: [" + action_name + "] NOT Found");
                return false
            }

            var performer = action.performer,
                params = action.params,
                interesting = params.interesting,
                data_collector = $$.is_defined(action.data_collector)
                    ? action.data_collector
                    : function () {
                        return self._render_data(name, function (item) {
                            return item.data.uuid;
                    }, false);
                },
                data = data_collector();

            performer = window[performer];
            performer(name, key_name, data, params);
        },

    update_view_model: function(name) {
        var view = this.views[name],
            view_model = view.view_model;

            if (! $$.is_defined(view_model)){
                return
            }

            var types = view.types,
                titles = $$.is_defined(view.titles) ? view.titles : [],
                tr_start = $$.is_defined(types._tr_start_)  ? types._tr_start_  : "<tr>",
                tr_stop =  $$.is_defined(types._tr_stop_)   ? types._tr_stop_   : "</tr>",
                tl_start = $$.is_defined(titles._tr_start_) ? titles._tr_start_ : "<tr>",
                tl_stop =  $$.is_defined(titles._tr_stop_)  ? titles._tr_stop_  : "</tr>",
                title_template = "",
                item_template = "",
                data_titles = {};

            view.search_fields = [];

            for (var i=0; i<view_model.length; i+=1) {
                var item = view_model[i],
                    field_name = item.name,
                    title = item.title || field_name ,
                    item_type = item.type,
                    data_item_template = item.data_template || item_type || '_',
                    title_item_template = item.title_template || item_type || '_',
                    sortable_types = view.sortable_types,
                    searchable_types = view.searchable_types,
                    title_field_template = titles[title_item_template],
                    data_field_template = types[data_item_template],
                    sortable = $$.includes(sortable_types, item_type) || $$.contains_string(item.params,"sort"),
                    searchable = $$.includes(searchable_types, item_type) || $$.contains_string(item.params,"search");

                if (searchable) {
                    view.search_fields.push(field_name)
                }

                title_field_template = $$.replace_word(title_field_template, "ITEM", field_name);
                title_field_template = $$.replace_word(title_field_template, "KIND", name);

                data_field_template = $$.replace_word(data_field_template, "ITEM", field_name);
                data_field_template = $$.replace_word(data_field_template, "KIND", name);

                item_template += data_field_template;
                title_template += title_field_template;

                data_titles[field_name] = {
                    idx: i,
                    title: title,
                    sort: sortable,
                    type: item_type,
                    info: item,
                    name: field_name
                };

            }
            view.title_data = data_titles;
            view.templates.list_view = tr_start +  item_template + tr_stop;
            view.templates.list_title = tl_start +  title_template + tl_stop;

            view.title_displayed = false;
            this.columns_number_reconciliation(name);

            // console.log("TITLE TEMPLATE: ", view.templates.list_title);
            // console.log("DATA  TEMPLATE: ", view.templates.list_view);
            // console.log("DATA  TITLE: ", view.title_data);
    },
    field_index_by_model : function(view_model, field_name) {
        for (var i=0; i<view_model.length; i+=1) {
            if (view_model[i].name === field_name) {
                return i;
            }
        }
    },
    hide_column: function(name, field_name) {
            var view = this.views[name],
                view_model = view.view_model,
                whole_view_model = $$.is_defined(view.whole_view_model) ? view.whole_view_model : $$.deep_copy(view_model),
                index = this.field_index_by_model(view_model, field_name);

            view_model.splice(index, 1);
            view.whole_view_model = whole_view_model;

            this.update_view_model(name);
            this._render(name);
    },
    move_column: function(name, field_name, direction) {
            var view = this.views[name],
                view_model = view.view_model,
                dir = direction === 'left' ? -1 : 1,
                original_position = this.field_index_by_model(view_model, field_name);

            view.view_model = $$.shift_element(view_model, original_position, dir);

            this.update_view_model(name);
            this._render(name);
    },
    init_config: function(kind, config) {
            if (! $$.is_defined(window.renderers)) {
                window.renderers = {}
            }
            config.translation = $$.is_defined(config.translation) ? config.translation : function() {return {}};

            window.renderers[kind] = {
                config: config,
                // todo - refactor / remove below
                card_template: config.card_template,
                edit_template: config.edit_template
            };

            $tablerender.add_view(window.renderers[kind].config);
            $tablerender.on_render(kind, function(view) {
                if ($$.is_defined(view.page_info)) {
                    $("#current_page_id" + kind).text(view.page_info.page);
                    $("#total_pages_id" + kind).text(view.page_info.pages);
                }
            });

            if ($$.is_defined(config.view_model)) {
                $tablerender.update_view_model(kind, config.view_model);
            }

            $tablerender.render(kind);
        },
        update_columns_number: function (name, delta) {
            var view = this.views[name],
                stretched_columns = $$.is_defined(view.stretched_columns) ? view.stretched_columns : [],
                colspan = "colspan";

            stretched_columns.forEach(function (element_id) {
                var cols = parseInt($$.get_attr($$.as_id_selector(element_id), colspan));
                console.log("COLS: <" + element_id + "> [" + cols + "] delta: [" + delta + "]");
                $$.set_attr($$.as_id_selector(element_id), colspan, Math.max(0, cols + delta))
            });

        },
        columns_number_reconciliation: function(name) {
            var view = this.views[name],
                model = view.model || $$.object_attr(view.meta, 'model', []),
                actual_columns_number = parseInt(model.length),
                current_columns_number = parseInt(view.current_columns_number);
            if (actual_columns_number > 0) {
                this.update_columns_number(name, actual_columns_number - current_columns_number);
                view.current_columns_number = actual_columns_number;
            }
        },
    }

})();

