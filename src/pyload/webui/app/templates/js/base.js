/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS104: Avoid inline assignments
 * DS207: Consider shorter variations of null checks
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */

{% autoescape true %}

// External scope
var root = this;

let desktopNotifications;
let interactiveCaptchaHandlerInstance = null;

// helper functions
const humanFileSize = function(size) {
    const filesizename = new Array("B", "KiB", "MiB", "GiB", "TiB", "PiB");
    const loga = Math.log(size) / Math.log(1024);
    const i = Math.floor(loga);
    const a = Math.pow(1024, i);
    if (size === 0) { return "0 B"; } else { return ((Math.round((size * 100) / a) / 100) + " " + filesizename[i]); }
};


const parseUri = function() {
    const oldString = $("add_links").value;
    const regxp = new RegExp('(ht|f)tp(s?):\/\/[a-zA-Z0-9\-\.\/\?=_&%#]+[<| |\"|\'|\r|\n|\t]{1}', 'g');
    const resu = oldString.match(regxp);
    if (resu === null) { return; }
    let res = "";

    for (let part of Array.from(resu)) {
        if (part.indexOf(" ") !== -1) {
            res = res + part.replace(" ", " \n");
        } else if (part.indexOf("\t") !== -1) {
            res = res + part.replace("\t", " \n");
        } else if (part.indexOf("\r") !== -1) {
            res = res + part.replace("\r", " \n");
        } else if (part.indexOf("\"") !== -1) {
            res = res + part.replace("\"", " \n");
        } else if (part.indexOf("<") !== -1) {
            res = res + part.replace("<", " \n");
        } else if (part.indexOf("'") !== -1) {
            res = res + part.replace("'", " \n");
        } else {
            res = res + part.replace("\n", " \n");
        }
    }

    return $("add_links").value = res;
};


Array.prototype.remove = function(from, to) {
    let left;
    const rest = this.slice(((to || from) + 1) || this.length);
    this.length = (left = from < 0) != null ? left : this.length + {from};
    if (this.length === 0) { return []; }
    return this.push.apply(this, rest);
};


document.addEvent("domready", function() {

    // global notification
    root.notify = new Purr({
        'mode': 'top',
        'position': 'center'
    });

    root.captchaBox = new MooDialog({destroyOnHide: false});
    root.captchaBox.setContent($('cap_box'));

    root.addBox = new MooDialog({destroyOnHide: false});
    root.addBox.setContent($('add_box'));

    $('add_form').onsubmit = function() {
        $('add_form').target = 'upload_target';
        if (($('add_name').value === "") && ($('add_file').value === "")) {
            alert('{{_("Please Enter a packagename")}}');
            return false;
        } else {
            root.addBox.close();
            return true;
        }
    };

    $('add_reset').addEvent('click', () => root.addBox.close());

    $('action_add').addEvent('click', function() { $("add_form").reset(); return root.addBox.open(); });
    $('action_play').addEvent('click', () => new Request({method: 'get', url: '/api/unpause_server'}).send());
    $('action_cancel').addEvent('click', () => new Request({method: 'get', url: '/api/stop_all_downloads'}).send());
    $('action_stop').addEvent('click', () => new Request({method: 'get', url: '/api/pause_server'}).send());


    // captcha events

    $('cap_info').addEvent('click', function() {
        load_captcha("get", "");
        return root.captchaBox.open();
    });
    $('cap_reset').addEvent('click', () => root.captchaBox.close());
    $('cap_form').addEvent('submit', function(e) {
        submit_captcha();
        return e.stop();
    });

    $('cap_positional').addEvent('click', on_captcha_click);

    return new Request.JSON({
        url: '/json/status',
        onSuccess: LoadJsonToContent,
        secure: false,
        async: true,
        initialDelay: 0,
        delay: 4000,
        limit: 3000
    }).startTimer();
});


var LoadJsonToContent = function(data) {
    $("speed").set('text', humanFileSize(data.speed)+"/s");
    $("aktiv").set('text', data.active);
    $("aktiv_from").set('text', data.queue);
    $("aktiv_total").set('text', data.total);

    if (data.captcha) {
        if ($("cap_info").getStyle("display") !== "inline") {
            $("cap_info").setStyle('display', 'inline');
            root.notify.alert('{{_("New Captcha Request")}}', {
                    'className': 'notify'
                  });
        }
    } else {
        $("cap_info").setStyle('display', 'none');
    }


    if (data.download) {
        $("time").set('text', ' {{_("on")}}');
        $("time").setStyle('background-color', "#8ffc25");
    } else {
        $("time").set('text', ' {{_("off")}}');
        $("time").setStyle('background-color', "#fc6e26");
    }

    if (data.reconnect) {
        $("reconnect").set('text', ' {{_("on")}}');
        $("reconnect").setStyle('background-color', "#8ffc25");
    } else {
        $("reconnect").set('text', ' {{_("off")}}');
        $("reconnect").setStyle('background-color', "#fc6e26");
    }

    return null;
};


const set_captcha = function(data) {
    $('cap_id').set('value', data.id);
    if (data.result_type === 'textual') {
        $('cap_textual_img').set('src', data.params.src);
        $('cap_title').set('text', '{{_("Please read the text on the captcha")}}');
        $('cap_submit').setStyle('display', 'inline');
        $('cap_textual').setStyle('display', 'block');
        return $('cap_positional').setStyle('display', 'none');

    } else if (data.result_type === 'positional') {
        $('cap_positional_img').set('src', data.params.src);
        $('cap_title').set('text', '{{_("Please click on the right captcha position")}}');
        $('cap_submit').setStyle('display', 'none');
        return $('cap_textual').setStyle('display', 'none');
    } else if (a.result_type === "interactive") {
        $("#cap_box #cap_title").text("");
        if(interactiveCaptchaHandlerInstance == null) {
            interactiveCaptchaHandlerInstance = new interactiveCaptchaHandler("cap_interactive_iframe", "cap_interactive_loading", submit_interactive_captcha);
        }
        if(data.params.url !== undefined && data.params.url.indexOf("http") === 0) {
            $("#cap_interactive").css("display", "block");
            interactiveCaptchaHandlerInstance.startInteraction(data.params.url, data.params);
        }
    }

};


var load_captcha = (method, post) =>
    new Request.JSON({
        url: '/json/set_captcha',
        onSuccess(data) { if (data.captcha) { return set_captcha(data); } else { return clear_captcha(); } },
        secure: false,
        async: true,
        method
    }).send(post);


var clear_captcha = function() {
    $('cap_textual').setStyle('display', 'none');
    $('cap_textual_img').set('src', '');
    $('cap_positional').setStyle('display', 'none');
    $('cap_positional_img').set('src', '');
    $("#cap_interactive").setStyle("display", "none");
    $("#cap_submit").setStyle("display", "none");
    $("#cap_interactive_iframe").attr("src", "").setStyle({display: "none", top: "", left: ""})
        .parent().setStyle({height: "", width: ""});
    if(interactiveCaptchaHandlerInstance) {
        interactiveCaptchaHandlerInstance.clearEventlisteners();
        interactiveCaptchaHandlerInstance = null;
    }
    return $('cap_title').set('text', '{{_("No Captchas to read")}}');
};


var submit_captcha = function() {
    load_captcha("post", `cap_id=${$('cap_id').get('value')}&cap_result=${$('cap_result').get('value')}` );
    return $('cap_result').set('value', '');
};


var on_captcha_click = function(e) {
    const position = e.target.getPosition();
    const x = e.page.x - position.x;
    const y = e.page.y - position.y;
    $('cap_result').value = x + "," + y;
    return submit_captcha();
};

// This function is called when the iframe is loaded, and it activates the link grabber of the tampermonkey script
interactiveCaptchaHandler.prototype.iframeLoaded = function(e) {
    var interactiveHandlerInstance = e.data;
    if(interactiveHandlerInstance._active) {
        var requestMessage = {
            actionCode: interactiveHandlerInstance.actionCodes.activate,
            params: interactiveHandlerInstance._params};
        // Notify TamperMonkey so it can do it's magic..
        $("#" + interactiveHandlerInstance._iframeId).get(0).contentWindow.postMessage(JSON.stringify(requestMessage),"*");
    }
};

interactiveCaptchaHandler.prototype.startInteraction = function(url, params) {
    // Activate
    this._active = true;

    this._params = params;

    $("#" + this._iframeId).attr("src", url);
};

// This function listens to messages from the TamperMonkey script in the iframe
interactiveCaptchaHandler.prototype.windowEventListener = function(e) {
    var interactiveHandlerInstance = e.data;
    var requestMessage = JSON.parse(e.originalEvent.data);

    if(requestMessage.actionCode === interactiveHandlerInstance.actionCodes.submitResponse) {
        // We got the response! pass it to the callback function
        interactiveHandlerInstance._captchaResponseCallback(requestMessage.params.response);
        interactiveHandlerInstance.clearEventlisteners();

    } else if(requestMessage.actionCode === interactiveHandlerInstance.actionCodes.activated) {
        $("#" + interactiveHandlerInstance._loadingid).css("display", "none");
        $("#" + interactiveHandlerInstance._iframeId).css("display", "block");

    } else if (requestMessage.actionCode === interactiveHandlerInstance.actionCodes.size)  {
        var $iframe = $("#" + interactiveHandlerInstance._iframeId);
        var width = requestMessage.params.rect.right - requestMessage.params.rect.left;
        var height = requestMessage.params.rect.bottom - requestMessage.params.rect.top;
        $iframe.css({top : - requestMessage.params.rect.top + "px",
            left : - requestMessage.params.rect.left + "px"})
            .parent().width(width).height(height);
    }
};

interactiveCaptchaHandler.prototype.clearEventlisteners = function() {
    // Deactivate
    this._active = false;

    // Clean up event listeners
    $("#" + this._iframeId).off("load", this.iframeLoaded);
    $(window).off('message', this.windowEventListener);
};

// Action codes for communication with iframe via postMessage
interactiveCaptchaHandler.prototype.actionCodes = {
    activate: "pyloadActivateInteractive",
    activated: "pyloadActivatedInteractive",
    size: "pyloadIframeSize",
    submitResponse: "pyloadSubmitResponse"
};

{% endautoescape %}
