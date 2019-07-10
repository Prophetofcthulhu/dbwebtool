(function () {
    'use strict';

    var _add_line_default = function(text, wsevent, message_area) {
        console.log(text);
        var html = message_area.html();
        message_area.html(html + '<br>' + text);
    };

    var chat = {
        mysocket: null,
        input_area: null,
        output_area: null,
        add_line: null,
        //user_id: null,
        out_audio: null,

        init: function(socket_for_text, add_line_method, input_area, output_area) {
            this.mysocket = this.init_mysocket(socket_for_text);
            this.add_line = add_line_method;
            this.output_area = output_area;
            this.input_area = input_area;
        },
        init_mysocket: function(mysocket) {
            var self = this;
            mysocket.on_text_message = self.display_text_message;
            mysocket.on_media_message = self.display_media_message;
            return  mysocket
        },
        connect_as: function(user_id) {
            this.mysocket.connect(user_id)
        },
        disconnect: function() {
            this.mysocket.disconnect()
        },
        possible_rooms: function(ws_event) {
            var result = [];
            for (var i=0; i < ws_event.rooms.length; i+=1) {
                var room = ws_event.rooms[i];
                if (room) {
                    result.push(room.name)
                }
            }
            return "room:" + result
        },
        display_text_message: function(raw_wsevent) {
            var self = this,
                ws_event = JSON.parse(raw_wsevent.data);

            console.log("EVENT:", ws_event);

            switch (ws_event.type) {
                case 'user.connect':
                    chat.add_line("You've connected as: [" + ws_event.nickname + "]", ws_event, chat.output_area);
                    chat.add_line("Possible rooms: [" + chat.possible_rooms(ws_event) + "]", ws_event, chat.output_area);
                    break;
                case 'message.im':
                    chat.add_line(ws_event.nickname + ": " + ws_event.text, ws_event, chat.output_area);
                    break;
            }
        },
        display_media_message: function(event) {
            var self = this;
            console.log("*** BINARY EVENT ***");
            // if (self.out_audio) {
            //     var context = self.out_audio.context,
            //         element = self.out_audio.element;
            //     $audio_processor.playStreamSound(context, event.data)
            // }
        },
        go: function(text) {
            //var value = this.message.text();
            console.log("VAL:[" + 'value' + "]");
            this.add_line(text, {}, this.output_area);
            this.mysocket.send(text)
        },

        keyup: function () {
            var self = this;
            var ev = window.event,
                key = ev.key,
                el = ev.target,
                entered_str = el.value;
            if (key === 'Enter') {
                //console.log("GOOOooo");
                self.go(entered_str);
                el.value = "";
            }
            // console.log(entered_str);
            // console.log(key, ev, el)
        },

        add_line_implementation: function(text, ws_event, messages_area) {
            //alert("chat_message append_translate_message [" + text + "]");
            //this.display_text_message(event);
            _add_line_default(text, ws_event, messages_area)
        }
    };
    window.$chat = chat;
})();
