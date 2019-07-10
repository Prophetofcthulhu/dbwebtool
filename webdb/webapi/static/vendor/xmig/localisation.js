(function () {
    // usage:
    // translation: $i18.get_translation
    'use strict';

    var i18 = {
        curr_lang: "xx",
        localisations: {
            "xx": {"test": "TEST"}  // dummy entry
        },

        load_localisation: function (lang, success) {
            var self = this;
            $.getJSON("/static/language/" + lang + ".json", function (data) {
                self.localisations[lang] = data;
                self.curr_lang = lang;
                if  ($$.is_defined(success)) {
                    success();
                }
            });
        },
        get_translation: function () {
            var self = i18;
            return self.localisations[self.curr_lang].translation;
        }

    };

    window.$i18 = i18;
})();




