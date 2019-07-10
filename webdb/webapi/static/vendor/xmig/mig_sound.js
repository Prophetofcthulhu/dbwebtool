    function sound_preprocess(sound) {
        return $$.first_char(sound) === '/' ? $$.skip_first_char(sound) : sound;
    }
