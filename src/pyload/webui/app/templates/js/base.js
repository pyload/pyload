{% autoescape true %}
const thisScript = document.currentScript;

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
    window.notify = new Purr({
        'mode': 'top',
        'position': 'center'
    });

    window.captchaBox = new MooDialog({destroyOnHide: false});
    window.captchaBox.setContent($('cap_box'));

    window.addBox = new MooDialog({destroyOnHide: false});
    window.addBox.setContent($('add_box'));

    $('add_form').onsubmit = function() {
        $('add_form').target = 'upload_target';
        if (($('add_name').value === "") && ($('add_file').value === "")) {
            alert('{{_("Please Enter a packagename")}}');
            return false;
        } else {
            window.addBox.close();
            return true;
        }
    };

    $('add_reset').addEvent('click', () => window.addBox.close());

    $('action_add').addEvent('click', function() { $("add_form").reset(); return window.addBox.open(); });
    $('action_play').addEvent('click', () => new Request({method: 'get', url: "{{url_for('api.rpc', func='unpause_server')}}"}).send());
    $('action_cancel').addEvent('click', () => new Request({method: 'get', url: "{{url_for('api.rpc', func='stop_all_downloads')}}"}).send());
    $('action_stop').addEvent('click', () => new Request({method: 'get', url: "{{url_for('api.rpc', func='pause_server')}}"}).send());


    // captcha events

    $('cap_info').addEvent('click', function() {
        load_captcha("get", "");
        return window.captchaBox.open();
    });
    $('cap_reset').addEvent('click', () => window.captchaBox.close());
    $('cap_form').addEvent('submit', function(e) {
        submit_captcha();
        return e.stop();
    });

    $('cap_positional').addEvent('click', on_captcha_click);

    if (thisScript.getAttribute('nopoll') !== "1") {
        return new Request.JSON({
            url: "{{url_for('json.status')}}",
            onSuccess: LoadJsonToContent,
            secure: false,
            async: true,
            initialDelay: 0,
            delay: 4000,
            limit: 3000
        }).startTimer();
    }
});


var LoadJsonToContent = function(data) {
    $("speed").set('text', humanFileSize(data.speed)+"/s");
    $("actives").set('text', data.active);
    $("actives_from").set('text', data.queue);
    $("actives_total").set('text', data.total);

    if (data.captcha) {
        if ($("cap_info").getStyle("display") !== "inline") {
            $("cap_info").setStyle('display', 'inline');
            window.notify.alert('{{_("New Captcha Request")}}', {
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
        $('cap_textual_img').set('src', data.src);
        $('cap_title').set('text', '{{_("Please read the text on the captcha")}}');
        $('cap_submit').setStyle('display', 'inline');
        $('cap_textual').setStyle('display', 'block');
        return $('cap_positional').setStyle('display', 'none');

    } else if (data.result_type === 'positional') {
        $('cap_positional_img').set('src', data.src);
        $('cap_title').set('text', '{{_("Please click on the right captcha position")}}');
        $('cap_submit').setStyle('display', 'none');
        return $('cap_textual').setStyle('display', 'none');
    }
};


var load_captcha = (method, post) =>
    new Request.JSON({
        url: "{{url_for('json.set_captcha')}}",
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

{% endautoescape %}
