var transcript_switch_class_name = 'transcript_switch_any';
var transcript_selected_class_name = 'transcript_selected';
var transcript_selected_mode = {script_vowel: 'anySubstring', script_consonant: 'anySubstring'};
var transcript_mode_as_id = {script_vowel: 'toggle_script_vowel_id', script_consonant: 'toggle_script_consonant_id'};


function get_another(group) {
    return group === 'script_vowel' ? 'script_consonant' : 'script_vowel'
}

function toogle_panel(classname, transcript_selected, element) {
    $(element).toggleClass(classname);
    if ($(element).hasClass(classname)) {
        $(".transcript_row").show();
        return "show"
    }
    else {
        $(".transcript_row").hide();
        $(".script_vowel").removeClass(transcript_selected);
        $(".script_consonant").removeClass(transcript_selected);
        return "hide"
    }
}

function toogle_transcript(element, name) {
    if (toogle_panel('transcript_selected_wrap', transcript_selected_class_name, element) === "hide") {
        $tablerender.remove_filter_group(name, 'script_vowel');
        $tablerender.remove_filter_group(name, 'script_consonant');
    }
    return false;
}

function toogle_exercises(element, name) {
    $("#exercises_row_id").toggle();
    return false;
}

function toogle_taglist(element, name) {
    $("#tagslist_id").toggle();
    return false;
}

function only_swap_single_filter(element, name, group) {
    var select_mode = transcript_selected_mode[group];

    $(element).toggleClass(transcript_selected_class_name);
    $tablerender.swap_filter(element, name, select_mode);
}

function sign_filter(element, name) {
    var group = $(element).hasClass('script_vowel') ? 'script_vowel' : 'script_consonant';
    if ($(element).hasClass(transcript_selected_class_name)) {
        only_swap_single_filter(element, name, group);
    }
    else {
        if (transcript_selected_mode[group] === 'startsWith') {
            $("." + group).removeClass(transcript_selected_class_name);
            $tablerender.remove_filter_group(name, group);
        }
        //console.log("SWAP 1 :" + group)
        only_swap_single_filter(element, name, group);
    }
    return false;
}

function selected_signs(group) {
    var res = [];
    $("." + group).each(function(i, el) {
        if ($(el).hasClass(transcript_selected_class_name)) {
            res.push(el)
        }
    });
    return res
}

function toggle_group(element, name, group) {
    $(element).toggleClass(transcript_switch_class_name);
    $("." + group).removeClass(transcript_selected_class_name);
    $tablerender.remove_filter_group(name, group);
}

function swap_transcript_mode(element, name, group) {
    var classname = transcript_switch_class_name,
        mode = null,
        selected = selected_signs(group),
        another_group = get_another(group),
        another_mode = transcript_selected_mode[another_group],
        another_element = transcript_mode_as_id[another_group];

    toggle_group(element, name, group);

    if ($(element).hasClass(classname)) {
        $(element).html('<i class="fa fa-ellipsis-v">');
        mode = "startsWith";
    }
    else {
        $(element).html('<i class="fa fa-ellipsis-h">');
        mode = "anySubstring";
    }
    transcript_selected_mode[group] = mode;

    if (selected.length === 1) {
         sign_filter(selected[0], name); // select the single filter back (but in new mode)
    }
    if (mode === "startsWith" && another_mode === "startsWith") {
        transcript_selected_mode[another_group] = "anySubstring";
        toggle_group(another_element, name, another_group);

        $("#" + another_element).html('<i class="fa fa-ellipsis-h">').removeClass(classname);
    }
    return false
}

// General Search
function set_search_mode(element, name) {
    var classname = 'search_any',
        mode = null;



    if ($(element).hasClass(classname)) {
        $(element).html('<i class="fa fa-ellipsis-v">');
        mode = "startsWith"
    }
    else {
        $(element).html('<i class="fa fa-ellipsis-h">');
        mode = "anySubstring";
    }
    $(element).toggleClass(classname);
    $tablerender.set_search_mode(element, name, mode)
}

function mark_line(el, mode, odd) {
    var  new_color = "";
    if (mode === "enter") {
        new_color =  "#eeeeee"
    }
    if (mode === "out") {
        new_color = odd === "true"  ?  "#f8f8f8" : "#ffffff"
    }
    $(el).css("background-color", new_color);

    return false
}

var card_panels = {};

var info_panel = function (kind, uuid) {
    var config = {
        autoplay: false,
        autonext: false,
        script: true,
        english: true,
        translation: true,
        viewsettings: false
    };
    card_panels[kind] =  new $Card().make_panel(kind, 'card_template', 300, 460, config, uuid, true);
    card_panels[kind].fix_item = function (row) {
            var script = row.script,
                colored_script = "";
            if (script) {
                var splits = script.split(/\s*/);
                for (var i=0; i<splits.length; i+=1) {
                    var s = splits[i];
                    colored_script += "<span class='script_" + s + "'>" + s + "</span>"
                }
            }
            row['colored_script'] = colored_script;

            data_item_pre_process(row, kind);
            return row
    };
    card_panels[kind].context = {sound_prefix: "/static/sound/"};
    card_panels[kind].on_close = function (card) {
        if ($$.is_defined(card._autonext_timeout)) {
            clearTimeout(card._autonext_timeout);
        }
    };
    card_panels[kind].render();
};

var _click_dalay = 0;
var info_panel_delay = function(kind, uuid) {
    kind = $tablerender.kind(kind);
    if (! _click_dalay) {
        info_panel(kind, uuid)
    }
};

var click_delay = function () {
    _click_dalay = 1;
    setTimeout(function () {
        _click_dalay = 0;
    }, 200)
};

// Edit panel
var edit_panel_config = {
    height: 500,
    wight: 480
};

var in_reload = false;
var reload_timeout = null;

var stop_actions = function (kind) {
    clearTimeout(reload_timeout);
    reload_timeout = null;
    console.log("STOP Actions")
};


var edit_panel = function (kind, uuid, mode) {
    mode = $$.is_defined(mode) ? mode : "edit";

    var config = {
        autoplay: false,
        autoapply: false,
        nextafterapply: false,
        viewsettings: false,
        viewextrainfo: false
    },

    skip_render = true,
    panel = new $Card().make_panel(kind, 'edit_template',
        edit_panel_config.height, edit_panel_config.wight, config, uuid, skip_render);

    card_panels[kind] = panel;

    panel.on_render = function (card) {
        card_item_highlight(kind, card.get_item_param("_removed_"), card.get_item());
        adjust_size(kind);
    };
    panel.on_close = function (card) {
        var item = card.get_item();
        if ($$.is_true(item._new_)) {
            if (! $$.is_defined(item._saved_) || ($$.is_defined(item._saved_) && item._saved_ !== "yes")) {
                //console.log("REMOVING TEMP", item);
                $tablerender.remove_item(kind, item.uuid, true)
            }
        }

        if ($$.is_defined(card._autonext_timeout)) {
            clearTimeout(card._autonext_timeout);
        }
        //stop_actions();
        //console.log("CLOSE ITEM", item)
    };
    panel.context = {
        sound_prefix: "/static/sound/",
        mode: mode
    };

    panel.fix_item = function (row) {
        data_item_pre_process(row, kind);
        return row
    };
    
    panel.render();
};


var page_config = function(kind) {
    console.log("***CONGIG [" + kind + "]", window.renderers);
    return window.renderers[kind].config
};

var get_card = function (kind) {
    return card_panels[kind]
};

var card_item_next = function(kind) {
    card_panels[kind].next_card_item()
};
var card_item_prev = function(kind) {
    card_panels[kind].previous_card_item()
};
var card_item_toggle_param = function(kind, param) {
    var need_render = ! card_panels[kind].get_param('autonext');
    return card_panels[kind].toggle_param(param, need_render)
};
var card_item_toggle_item = function(kind, param) {
    var need_render = ! card_panels[kind].get_param('autonext');
    card_panels[kind].toggle_item(param, need_render, true)
};
var card_item_set_item = function(kind, param, value, need_render) {
    card_panels[kind].set_item(param, value, need_render)
};
var send_save = function(kind, data, success, mode) {
    mode = $$.is_defined(mode) ? mode : "edit";
    var url = '/materials/edit/' + kind + "/";
    $ax.XLoadJson(url, "POST", data, success || function (data) {})
};


var auto_expand = function(kind) {
    card_item_toggle_param(kind, 'autoapply');

    if (reload_timeout) {
        console.log("in progress. Skip")
    }
    else {
        var panel = card_panels[kind],
            start_idx = panel.get_current_index(),
            stop_idx = panel.get_max_current_index(),
            uuids = [],
            i;

        for (i = start_idx; i < stop_idx; i += 1) {
            var index = panel.get_item_by_index(i),
                item = $tablerender.item_by_index(kind, index);
            uuids.push(item.uuid)
        }

        console.log("uuids", uuids);
        i = -1;

        reload_timeout = setInterval(function () {
            if (in_reload) {
                console.log("Waiting...");
                return;
            }
            i += 1;
            if (i < uuids.length) {
                var uuid = uuids[i];

                //console.log("Perform [" + i + "] [" + uuid + "]...");

                edit_panel(kind, uuid);
                var reload_button_id = "reload_button" + kind,
                    el = document.getElementById(reload_button_id);

                in_reload = true;
                card_item_reload(el, kind, uuid, function (mode) {
                    console.log("Item preformed. [" + kind + "] UUID: [" + uuid + "] Mode: [" + mode + "]");
                    in_reload = false;
                    card_item_just_apply(kind);
                    card_item_cancel(kind, "skip_stop");
                });
            }
            else {
                console.log("Completed all items...");
                clearTimeout(reload_timeout);
                reload_timeout = null;
            }

        }, 500);

    card_item_cancel(kind, "skip_stop");
    }

};


var purge_button = function (need_to_purge, kind) {
    $("#purge_id"+kind).prop("disabled", ! need_to_purge);
    if (need_to_purge) {
        $("#purge_id"+kind+"_icon").addClass("fa-circle-o").removeClass("fa-circle-thin");
    }
    else {
        $("#purge_id"+kind+"_icon").addClass("fa-circle-thin").removeClass("fa-circle-o");
    }
};

var purge = function (kind) {
    var url = '/materials/purge/' + kind + "/";
    $ax.XLoadJson(url, "GET", {}, function (data) {});
    purge_button(false, kind);
};

var card_item_cancel = function(kind, skip_stop) {
    if (card_panels[kind].get_item_param("_removed_")) {
        card_panels[kind].set_item("_removed_", false)
    }
    if (! $$.is_defined(skip_stop)) {
        stop_actions(kind)
    }
    card_panels[kind].close()
};

var card_item_highlight = function(kind, disabled, item) {
    var save_button =  $("#do_save" + kind),
        apply_button = $("#do_apply" + kind),
        cancel_button = $("#do_cancel" + kind),
        delete_button = $("#do_remove" + kind);

    delete_button.text(disabled ? "Restore" : "Delete");

    if (disabled) {
        delete_button.addClass("btn-warning").removeClass("btn-danger");
        apply_button.addClass("btn-danger").removeClass("btn-primary");
        save_button.addClass("btn-danger").removeClass("btn-primary");
    }
    else {
        delete_button.addClass("btn-danger").removeClass("btn-warning");
        apply_button.addClass("btn-primary").removeClass("btn-danger");
        save_button.addClass("btn-primary").removeClass("btn-danger");
    }

    $$.scan_forms_element("edit_" + kind, function (element) {
        element.prop("disabled", disabled);
        element.css("text-decoration", disabled ? "line-through" : "inherit")
    });
};

var card_item_delete = function(el, kind, uuid) {
    var disabled = $.trim($(el).text()) === "Delete",
        panel = card_panels[kind];

    card_item_highlight(kind, disabled, panel);
    if(disabled) {
        panel.set_item("_removed_", true, false);
    }
    else {
        panel.set_item("_removed_", false, false);
        $tablerender.restore_record(kind, uuid);
        if (panel.get_item_param("_saved_")) {
            var config = page_config(kind),
                fields = config.model,
                data = $$.filtered_fields(panel.get_item(), fields);

            data["_restored_"] = true;
            panel.set_item("_saved_", false, false);
            send_save(kind, {data: JSON.stringify(data)});
        }
    }
};

var adjust_size = function (kind) {
    var item = card_panels[kind].get_item(),
        viewsettings = card_panels[kind].get_param('viewsettings'),
        viewextrainfo = card_panels[kind].get_param('viewextrainfo'),
        base_size = edit_panel_config.height,
        add_size = 0,
        number_sounds = $$.is_defined(item.extra_sounds && item.extra_sounds.sounds) ? item.extra_sounds.sounds.length : 0;

    if (viewextrainfo)  { add_size += number_sounds * 16; }
    if (viewsettings)   { add_size += 110 }
    card_panels[kind].set_size(edit_panel_config.wight, base_size + add_size);
};

var model_update = function (kind, data) {
    var sound_info = data.sounds,
        sounds = sound_info.sounds,
        folder = sound_info.folder,
        number_sounds = sounds.length;


    card_panels[kind].set_item('extra_sounds', sound_info, false);
    card_panels[kind].set_item('sound_folder', folder, false);

    adjust_size(kind, number_sounds);
};

var card_item_view_extra_info = function(el, kind, mode) {
    card_item_toggle_param(kind, 'viewextrainfo');
    adjust_size(kind);
    card_panels[kind].render()
};

var card_item_reload = function(el, kind, uuid, on_compete_function) {
    if ($$.is_true(card_panels[kind].get_item_param("_new_"))) {
        card_item_just_apply(kind);
    }

    var e = $(el),
        panel = card_panels[kind],
        item = card_panels[kind].get_item(),
        form_data = card_item_collect(kind),
        en = form_data.en,
        ru = form_data.ru,
        image = form_data.image,
        word = $$.trim(en),
        lang = "en",
        existed_item = null,
        sound = form_data.sound;

    if (word === '' || word === '(new)') {
        lang  = 'ru';
        word = ru;
    }
    if (panel.get_item_param("_new_") === "yes") {
        existed_item = $tablerender.find_param(kind, lang, word);
    }

    if (existed_item && existed_item.sound_folder !== "en/n/new/") {
        if (! e.hasClass("error")) {
            //console.log("EXISTS", word, lang, existed_item);
            e.addClass("error");
            if($$.is_function(on_compete_function)) { on_compete_function("exists") }
            return;
        }
        console.log("EXISTS. Making duplicate");
    }

    if ($$.trim(word) === '') {
        console.log("Noting for processing", word, en, ru);
        if($$.is_function(on_compete_function)) { on_compete_function("noting") }
        return;
    }
    e.addClass("fa-spin");

    //console.log("CARD DATA", form_data)

    var req = {uuid: uuid, action: "refresh", word: word, sound: sound, lang: lang, ru: ru, image: image};

    send_save(kind,  {action: JSON.stringify(req)}, function (data) {
        //console.log("ADD DATA", data);

        e.removeClass("fa-spin");

        var kind = data.kind;
        card_item_update(kind, data);
        model_update(kind, data);
        item.extra_sounds = data.sounds;
        item.images = data.images;
        item.picuture = data.image;
        mark_current_sound(kind, "update_default");
        card_panels[kind].set_param('viewextrainfo',true);
        panel.render();

        if($$.is_function(on_compete_function)) {
            setTimeout(function () {
                on_compete_function("loaded") }, 200);
        }
    });

};


var add_record = function (kind) {
     var config = page_config(kind),
         model = config.model,
         item = $tablerender.new_record(kind, null, model, true);
    edit_panel(kind, item.uuid, "new")
};

var card_settings = function(el, kind, settigs_panel_id, uuid) {
    var p = $($$.as_id_selector(settigs_panel_id)),
        card = get_card(kind);

    if (card_item_toggle_param(kind, 'viewsettings')) {
        p.show();
    }
    else {
        p.hide();
    }
};

var card_item_clone = function(kind, uuid) {
         var config = page_config(kind),
         model = config.model,
         item = $tablerender.new_record(kind, uuid, model, true);

    card_panels[kind].render();
    //console.log("CLONED AS ", item)
};

var card_item_mass = function(kind) {
     var config = page_config(kind),
     model = config.model;

    $("#item_insert_panel_id").toggle();
    $("#mass_insert_panel_id").toggle();
    $("#edit_buttons_normal_id").toggle();
    $("#edit_buttons_massins_id").toggle();

};

var mass_insert_just_apply = function(kind) {
    var keyfield = "uuid",
        formname = "massinsert_" + kind,
        fields = ["name", "tags", "rules", "content"],
        data = {};



    for (var i = 0; i < fields.length; i += 1) {
        var fieldname = fields[i];
        if ($$.is_defined(document.forms[formname][fieldname])) {
            var value = document.forms[formname][fieldname].value;
            console.log("FIELD [" + fieldname + "]", value);
            data[fieldname] = value
        }
    }

    send_save("_MASSINSERT_", {data: JSON.stringify(data)}, function (data) {
        console.log(data)
    });

};

var toggle_image_sound_panel = function(el, kind) {
    $("#images_edit_panel").toggle();
    $(".sound_edit_panel").toggle();
    $(el).toggleClass("fa-file-audio-o").toggleClass("fa-file-picture-o");
};

var mass_insert_save = function(kind) {
  mass_insert_just_apply(kind)
};

var mass_insert_apply = function(kind) {
    mass_insert_just_apply(kind)
};


var parent_render = function (kind) {
    card_panels[kind].parent_render()
};


var card_item_collect = function(kind) {
    var formname = "edit_" + kind,
        config = page_config(kind),
        fields = config.model,
        data = {};

    for (var i = 0; i < fields.length; i += 1) {
        var fieldname = fields[i];
        if ($$.is_defined(document.forms[formname][fieldname])) {
            data[fieldname] = document.forms[formname][fieldname].value;
        }
        console.log("FORMNAME.fieldname ", formname, fieldname, data[fieldname], data);
    }
    //console.log("COLLECT OK", formname);
    return data
};

var card_item_update = function (kind, data) {
    var formname = "edit_" + kind,
        config = page_config(kind),
        fields = config.model,
        item = card_panels[kind].get_item();

    for (var i = 0; i < fields.length; i += 1) {
        var fieldname = fields[i];
        if ($$.is_defined(document.forms[formname]) && $$.is_defined(document.forms[formname][fieldname])) {
            if (document.forms[formname][fieldname].value !== '') {
                //console.log("UPDATED FIELD [" + fieldname + "] IS NOT EMPTY.  *** SKIPPED *** [" + document.forms[formname][fieldname] + "]" );
                continue
            }
            var value = data[fieldname];
            if ($$.is_defined(value)) {
                document.forms[formname][fieldname].value = value;
                item[fieldname] = value;
                //console.log("UPDATED FIELD [" + fieldname + "] as ", value);
            }
        }
    }
};


var update_new_default_sound = function(item, value) {
    //console.log("ITEMMMM 0", item)
    if ($$.is_defined(item.extra_sounds) && $$.is_defined(item.extra_sounds.sounds)) {
        for (var i=0; i<item.extra_sounds.sounds.length; i+=1) {
            var sound = item.extra_sounds.sounds[i],
                uuid = sound.uuid,
                folder = item.extra_sounds.folder;

            sound.current = false;
            //console.log("UUID/VALUE", uuid, value);
            if (uuid === value) {
                sound.current = true;
                item.sound = $$.normalise_url(folder + "/" + sound.sound);
                //console.log("UPDATED UUID/VALUE", uuid, value);
            }
        }
    }
    //console.log("ITEMMMM 1", item);
};
var store_sound_selection = function (el, kind) {
    var formname = "edit_" + kind,
        uuid = $(el).val();
    document.forms[formname]["new_sound"].value = uuid;
};

var card_item_just_apply = function(kind) {
    var keyfield = "uuid",
        formname = "edit_" + kind,
        config = page_config(kind),
        fields = config.model,
        data = card_item_collect(kind),
        item = card_panels[kind].get_item();

    for (var i = 0; i < fields.length; i += 1) {
        var fieldname = fields[i];
        if ($$.is_defined(document.forms[formname][fieldname])) {
            var value = document.forms[formname][fieldname].value;
            //console.log("FIELD [" + fieldname + "]", value);

            if (fieldname === 'new_sound' && value !== '') {
                update_new_default_sound(item, value);
                data.sound = item.sound;
            }
            else {
                card_item_set_item(kind, fieldname, value, false);
            }
        }
    }

    if (card_panels[kind].get_item_param("_removed_")) {
        $tablerender.remove_record(kind, data[keyfield]);
        data["_removed_"] = true
    }
    card_panels[kind].set_item("_saved_", true, false);
    card_panels[kind].set_item("_new_", false, false);
    parent_render(kind);

    //console.log("ITEM", card_panels[kind].item());

    var sounds = card_panels[kind].get_item_param("extra_sounds");
    if ($$.is_defined(sounds)) {
        data.extra_sounds = sounds
    }

    //console.log("DATA", data);

    send_save(kind, {data: JSON.stringify(data)});
    purge_button(true, kind);
};


var card_item_apply = function(kind) {
    card_item_just_apply(kind);
    if(card_panels[kind].get_param('nextafterapply')) {
        card_item_next(kind)
    }
};

var card_item_save = function(kind) {
    card_item_just_apply(kind);
    card_panels[kind].close()
};

var mark_current_sound = function(kind, update_default) {
     var item = card_panels[kind].get_item(),
         extra_sounds = item.extra_sounds,
         sound = card_panels[kind].get_item_param('sound'),
         sound_folder = card_panels[kind].get_item_param('sound_folder'),
         update_sound = $$.is_defined(update_default),
         default_sound = "",
         default_index = 0,
         found = false;
     

     if ($$.is_defined(extra_sounds) && $$.is_defined(extra_sounds.sounds)) {
         var sounds = extra_sounds.sounds;
         for (var i=0; i<sounds.length; i+=1) {
            var mode = false,
                current_sound = $$.normalise_url(sound_folder + "/" +  sounds[i].sound);

            if (i === 0) {
                default_index = i;
                default_sound = current_sound;  // the first one - just implementation
            }
            if (current_sound === sound) {
                //console.log("CURRENT", sound, sounds[i].uuid);
                found = true;
                mode = true;
            }
            sounds[i].current = mode;
         }
         //console.log("SOUND    XXX   :", found, update_sound, default_sound, default_index);
         if (! found && update_sound) {

            if ($$.first_char(default_sound) === '/') {
                default_sound = $$.skip_first_char(default_sound);
                item.sound = default_sound;
            }
            sounds[default_index].current = true;
            //console.log("SOUND  UPDATED :", default_sound, default_index);
         }
     }
};


var data_item_pre_process = function(item, kind) {
     var sound_folder = item.sound,
         idx = sound_folder.lastIndexOf("/");

     if (idx !== -1) {
         sound_folder = sound_folder.substring(0, idx+1);
         item.sound_folder = sound_folder;

     }
     mark_current_sound(kind);
     return item
};


function woldlist_viewer_init(kind) {
    $tablerender.add_view(window.renderers[kind].config);
    $tablerender.render(kind);
    $tablerender.on_render(kind, function(view) {
        if ($$.is_defined(view.page_info)) {
            //console.log("VIEW", view.page_info);
            $("#current_page_id" + kind).text(view.page_info.page);
            $("#total_pages_id" + kind).text(view.page_info.pages);
            purge_button(view.addinfo.need_purge);
        }
    });

    $tablerender.on_clone(kind, function(item, action, base_item) {
        if (action === 'new') {
            item["en"] = "(new)";

            item["ru"]      = "";
            item["script"]  = "";
            item["pos"]     = "";
            item["sound_folder"] = "";
            item["sound"]   = "en/n/new/new_0007_None_p.mp3";
        }
        if (action === 'clone') {
            item["_cloned_"] = true;
            item["_id_"] = base_item["_id_"] + ".1";
            item["en"] = item["en"] + " (clone)";
        }
    });
}

// function sound_preprocess(sound) {
//     return $$.first_char(sound) === '/' ? $$.skip_first_char(sound) : sound;
// }

function configure(kind, config) {

    if (! $$.is_defined(window.renderers)) {
        window.renderers = {}
    }
    config.translation = $$.is_defined(config.translation) ? config.translation : function() {return {}};
    //config.template = config.template || _.template(config.view_template);
    //config.template = config.template || _.template(config.view_template);

    window.renderers[kind] = {
        config: config,
        //view_template: config.template,
        card_template: config.card_template,
        edit_template: config.edit_template
    };

    woldlist_viewer_init(kind);
}

function toggle_color(el, mode) {
    var  new_color = "";
    if (mode === "enter" || mode === 1) {
        new_color =  "cornflowerblue"
    }
    if (mode === "out" || ! mode) {
        new_color = "#cfcfcf"
    }
    $(el).css("background-color", new_color);

    return false
}

function filter_tag(el, name, tagid) {
    var view = $tablerender.views[name],
        data = view.data,
        filter_key = 'tg' + tagid;

    //console.log("FILTER TAG[" + name + "] [" + tagid + "]", data);
    var mode = $tablerender.toggle_filter(name, filter_key) ? "enter" : "out";
    toggle_color(el, mode)
}

function posit_to_item(name, uuid, index) {
    var view = $tablerender.views[name],
        data = view.data,
        page_size = view.page_size;

    view.events.postload.pop();

    if ($$.is_defined(uuid)) {
        for (var i=0; i< data.length; i+=1) {
        var item = data[i];
            if (item.uuid === uuid) {
                view.page = Math.floor(i / page_size);
                var shift = i % page_size;
                if (shift !== index) {
                    if (shift > index) {
                        view.index_shift = shift - index + 1;
                    }
                    else if (view.page > 0) {
                        view.page -= 1;
                        view.index_shift = page_size - index + shift + 1;
                    }
                }
            }
        }
    }
}

function switch_list(name, tagname, tagid, item_uuid, index) {
    console.log("switch_list [" + name + "] [" + tagname + "] [" + tagid + "] [" + item_uuid + "][" + index + "]");
    //document.location = "/materials/list/" + tagid;
    var view = $tablerender.views[name];
    view.events.postload.push(function() {
        posit_to_item(name, item_uuid, index)
    });
    $tablerender.load_other(name, "/materials/jsondb/"  + tagid);

    console.log("viewdb skipped for now - please fix");

    /*
    var extra_view_url = "/materials/viewdb/" + tagid + "/";
    $ax.XLoadJson(extra_view_url, "POST", {"a":"b"}, function (data) {
                console.log(data);
                if ($$.is_defined(data.menu_template)) {
                    $("#additional_menu_id").html(data.menu_template);
                }
            });
    */
    //$tablerender.load_other(name, "/materials/viewdb/"  + tagid)

}


function dict_by_id(tags) {
    var result = {};
    tags.forEach(function (item) {
        result[item.id] = item
    });
    return result;
}

function get_top_tag_idname(name) {
    var view = $tablerender.views[name];
    return view.toptag_idname;
}

function listinfo_expanding(name) {
    var view = $tablerender.views[name],
        data = view.data,
        addinfo = view.addinfo,
        tags = addinfo ? dict_by_id(addinfo.tags) : {};

        for (var index=0; index < data.length; index+=1) {
            var item = data[index],
                lists = item.lists || [],
                extended_lists = [];

            lists.forEach(function (id) {
                extended_lists.push(tags[id]);
                item['tg' + id] = true;
            });
            item.lists = extended_lists;
        }
}


function update_metakind_data(name) {
    //console.log("update_metakind_data")
    var view = $tablerender.views[name],
        interface_lang = view.interface_lang,
        addinfo = view.addinfo,
        titled_tags_all = addinfo.titled_tags,
        titled_tags_selected = [],
        res = "";

    titled_tags_all.forEach(function (item) {
        if (item.lang === interface_lang) {
            titled_tags_selected.push(item)
        }
    });

    titled_tags_selected.forEach(function (item) {
        item.kind = name;
        if (titled_tags_selected.length === 1) {
            res += _.template('<span class="listname_wrapper"><%= name %></span>' + ' ')(item);
        }
        else{
            res += _.template('<span onclick="switch_list(\'<%= kind %>\', \'<%= name %>\', \'<%= uuid %>\', \'\')" class="listname_wrapper"><%= name %></span>' + ' ')(item);
        }
    });

    $("#list_title_id").html(res);
}

function get_interface_lang(name) {
    var view = $tablerender.views[name];
    return view.interface_lang;
}

function addinfo_render(name) {
    var view = $tablerender.views[name],
        interface_lang = view.interface_lang,
        addinfo = view.addinfo,
        meta = addinfo.meta,
        tags = addinfo.tags,
        titled_tags = addinfo.titled_tags,
        titled_tags_ids = {},
        res = "";

    if ($$.is_defined(meta) && $$.is_defined(meta.view)) {
        view.view_mode = meta.view
    }
    if (! tags) {
        return
    }

    titled_tags.forEach(function (item) {
        titled_tags_ids[item.id]  = 1;
    });

    for (var i=0; i<tags.length; i+=1) {
        var item = tags[i];
        item.kind = name;

        if (item.name === view.toptag_name) {
            view.toptag_idname = "tg" + item.id;
        }

        // TODO REWRITE THIS BELOW!!!
        if (item.name === 'top' || item.name === "top-3000" || item.name === 'топ-3000') {
            continue
        }
        if (item.lang === interface_lang && titled_tags_ids[item.id] !== 1) {
            res += _.template('<span onclick="filter_tag(this, \'<%= kind %>\', \'<%= id %>\')" class="tag_wrapper"><%= name %></span>' + ' ')(item);
        }
    }
    $("#tagslist_content_id").html(res)
}

function extended_word_info(name, en, ru) {
    console.log("DISPLAY EXTRA INFO FOR WORD - Miller Dictionary will be here... [" + en + "] [" + ru + "], kind: [" + name + "]");
    var view = $tablerender.views[name],
    data = view.data;
}