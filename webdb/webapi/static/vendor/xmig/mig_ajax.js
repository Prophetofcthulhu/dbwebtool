// set of Ajax related utilities. Based on jQuiery
// copyright - Sergii Tretiak (tretyak@gmail.com) - MIT License

//Usage: $ax.function_name

(function () {
    'use strict';

    var MySys = {
        debug: false,
        error: false,
        errormsg: ""
    };

    window.$ax = MySys;

    MySys.showError = function(mess) {
        if (MySys.debug) {
            console.log(mess);
        }
    };

    MySys.AjaxErrorFn = function (xhr, status, exception) {
        MySys.errormsg = "Error! Action: 'Ajax request (" + this.url +  ")', Status: '" + status + "', Exception: '" + exception + "'";
        if(MySys.debug) {
            MySys.showError(MySys.errormsg);
        }
    };

    MySys.AjaxAlwaysFn = function (data, status) {
    };


    MySys.load_json = function(url, method, dataIn, successFn) {
        MySys.XLoad(url, method, "json", dataIn, successFn, MySys.AjaxErrorFn)
    };

    MySys.XLoad = function(url, method, data_type, dataIn, successFn, errorFn, alwaysFn) {
        $.ajax({
            type: method,
            method: method,
            url: url,
            data: dataIn,
            dataType: data_type,

            complete: alwaysFn,
            success: successFn,
            error:  errorFn
        });
    };

    MySys.load_text = function(url, dataIn, successFn) {
        MySys.XLoad(url, "GET", "text", dataIn, successFn, MySys.AjaxErrorFn, MySys.AjaxAlwaysFn)
    };


    MySys.load_json_compressed = function (url, method, dataIn, successFn) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            var data_bytes = SnappyJS.uncompress(new Uint8Array(this.response)),
                data_str = new TextDecoder().decode(data_bytes),
                data = JSON.parse(data_str);
                successFn(data)
            }
        };

         xhttp.open(method, url, true);
         xhttp.responseType = "arraybuffer";
         xhttp.send(dataIn);
        }
}());

