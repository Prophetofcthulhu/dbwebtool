(function () {
    // see https://github.com/joewalnes/reconnecting-websocket
    // see https://www.html5rocks.com/en/tutorials/webaudio/intro/
    'use strict';

    var _add_line_default = function(text, ws_event, messages) {
        console.log(text);
        var html = messages.html();
        messages.html(html + '<br>' + text);
    };

    var init_socket = function(socket, ws, mode) {
        ws.onclose = socket.on_close;
        ws.onmessage = mode === 'text' ? socket.on_text_message : socket.on_media_message
    };

    var scocket = {
        //scocket_base_url: 'ws://127.0.0.1:8886/ws',
        scocket_base_url: 'ws://127.0.0.1:8082/ws',
        ws: null,
        ready: false,
        messages: null,
        add_line: _add_line_default,
        user_id: null,
        out_audio: null,
        on_open: function() {},
        on_close: function() {},
        on_text_message: function(event) {},
        on_media_message: function(event) {},

        xinit: function(add_line_method, input_area, output_area) {
            this.add_line = add_line_method;
            this.messages = output_area;
            this.message = input_area;
        },
        init: function(base_url) {
            this.scocket_base_url = base_url;
            return this
        },
        go: function() {
            var value = this.message.text();
            //console.log("VAL:[" + value + "]");
            this.send(value)
        },
        reconnect: function (mode) {
            if (this.ws) {
                this.disconnect()
            }

            var self = this,
                suffix = this.user_id !== "" ?  "?user=" + this.user_id : "",
                url = this.scocket_base_url + suffix,
                params = {debug: true};

            if (mode === 'binary') {
                 params = {binaryType: 'arraybuffer'}
            }
            this.ws = new ReconnectingWebSocket(url, null, params);
            this.ws.onopen = function() {
                self.ready = true;
                console.log('WS opened');
            };
            console.log("WS Connected. mode: [" + mode + "] [" + url + "]")
        },
        connect: function (user_id) {
            //if (user_id) {
                this.user_id = user_id;
                this.reconnect("text");
                init_socket(this, this.ws, 'text');
            //}
        },
        reconnect_as: function (mode) {
            this.reconnect(mode);
            init_socket(this, this.ws, mode);
        },
        disconnect: function () {
            if (this.ws) {
                this.ws.close();
                this.ws = null;
                this.ready = false
            }
            console.log("WS Disconnected.")
        },
        send_event: function (ws_event) {
            if (this.ready) {
                this.ws.send(JSON.stringify(ws_event));
                console.log("message sent: ", ws_event)
            }
        },

        send: function (data) {
            if (data) {
                scocket.send_event(data);
            }
        },

        start_stream: function () {
            scocket.send_event({type: 'stream.start', text: ""});
            scocket.reconnect_as('binary');
        },
        stop_stream: function () {
            scocket.reconnect_as('text');
            scocket.send_event({type: 'stream.stop', text: ""});
        },
        streamdata: function (value, out_audio) {
            scocket.out_audio = out_audio;
            if (this.ready) {
                //console.log("streaming....");
                scocket.ws.send(value)
            }
        },
        user_type_message: function () {
            this.send_event({"type": "user.type"})
        }
    };

    window.$socket = scocket;
})();
