{% autoescape true %}

let desktopNotifications;
let interactiveCaptchaHandlerInstance = null;
const thisScript = document.currentScript;

function indicateLoad() {
    $(".load-indicator").css('opacity',1);
}

function indicateFinish() {
    $(".load-indicator").css('opacity',0);
}

function indicateSuccess(message) {
   if(message === undefined) {
      message = "{{_('Success')}}";
   }

    indicateFinish();
    mdtoast(message + '.', {position: "bottom center", type: "success", duration: 3000});
}

function indicateFail(message) {
   if(message === undefined) {
      message = "{{_('Failed')}}";
   }

    indicateFinish();
    mdtoast(message + '.', {position: "bottom center", type: "error", duration: 4000});
}

function humanFileSize(f) {
    var c, d, e, b;
    d = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"];
    b = Math.log(f) / Math.log(1024);
    e = Math.floor(b);
    c = Math.pow(1024, e);
    if (f === 0) {
        return "0 B";
    } else {
        return Math.round(f * 100 / c) / 100 + " " + d[e];
    }
}

function parseUri() {
    var b, c, g, e, d, f, a;
    var $add_links = $("#add_links");
    b = $add_links.val();
    g = new RegExp("(?:ht|f)tp(?:s?)://[a-zA-Z0-9-./?=_&%#:]+(?:[<| |\\\"|'|\\r|\\n|\\t]{1}|$)", "gi");
    d = b.match(g);
    if (d === null) {
        return $add_links.val("");
    }
    e = "";
    for (f = 0, a = d.length; f < a; f++) {
        c = d[f];
        if (c.indexOf(" ") !== -1) {
            e = e + c.replace(" ", " \n");
        } else {
            if (c.indexOf("\t") !== -1) {
                e = e + c.replace("\t", " \n");
            } else {
                if (c.indexOf("\r") !== -1) {
                    e = e + c.replace("\r", " \n");
                } else {
                    if (c.indexOf('"') !== -1) {
                        e = e + c.replace('"', " \n");
                    } else {
                        if (c.indexOf("<") !== -1) {
                            e = e + c.replace("<", " \n");
                        } else {
                            if (c.indexOf("'") !== -1) {
                                e = e + c.replace("'", " \n");
                            } else {
                                e = e + c.replace("\n", " \n");
                            }
                        }
                    }
                }
            }
        }
    }
    return $add_links.val(e);
}

Array.prototype.remove = function(d, c) {
    var a, b;
    a = this.slice((c || d) + 1 || this.length);
    this.length = (b = d < 0) != null ? b : this.length + {
        from: d
    };
    if (this.length === 0) {
        return [];
    }
    return this.push.apply(this, a);
};

function getScrollBarHeight() {
    var inner = document.createElement('p');
    inner.style.width = "200px";
    inner.style.height = "100%";

    var outer = document.createElement('div');
    outer.style.position = "absolute";
    outer.style.top = "0px";
    outer.style.left = "0px";
    outer.style.visibility = "hidden";
    outer.style.width = "150px";
    outer.style.height = "200px";
    outer.style.overflow = "hidden";
    outer.appendChild(inner);

    document.body.appendChild(outer);
    var w1 = inner.offsetHeight;
    outer.style.overflow = 'scroll';
    var w2 = inner.offsetHeight;
    if (w1 === w2) w2 = outer.clientHeight;

    document.body.removeChild(outer);

    return (w1 - w2);
}

$(function() {
    var $goto_top = $('#goto_top');
    var $stickyNav = $("#sticky-nav");
    var topbuttonVisible = $(window).scrollTop() > 100;

    $goto_top.toggleClass('hidden', !topbuttonVisible).affix({offset: {top:100}});

    $stickyNav.css(stickynavlCss($(window).scrollTop()));
    function stickynavlCss(scrollTop) {
        var $headPanel = $('#head-panel');
        var headpanelHeight = $headPanel.height();

        if (scrollTop <= headpanelHeight) {
            return {"display": "none"};
        } else if (scrollTop > headpanelHeight && scrollTop < headpanelHeight*2) {
            return {"display": "block", "top": (scrollTop - headpanelHeight*2) + "px"};
        } else {
            return {"display": "block", "top": "0"};
        }
    }

    $(window).scroll(function() {
        var scrollTop = $(this).scrollTop();
        var visible = Boolean(scrollTop > 100);

        if (topbuttonVisible !== visible) {
            $goto_top.toggleClass('hidden', !visible);
            topbuttonVisible = visible;
        }
        $stickyNav.css(stickynavlCss(scrollTop));
    });

    $goto_top.click(function () {
        $('html,body').animate({scrollTop:0},'slow');
        return false;
    });

    desktopNotifications = false;
    if ("Notification" in window) {
        if (Notification.permission === 'granted') {
            desktopNotifications = true;
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(function(result) {
                desktopNotifications = (result === 'granted');
            });
        }
    }

    var addlinksMinHeight = getScrollBarHeight() + Math.round(parseFloat($("#add_links").css("line-height").replace('px','')));
    var addlinksHeight;
    $("#modal-content").resizable({
        minHeight: 520 + addlinksMinHeight,
        minWidth: 310,
        start: function (event, ui) {
            addlinksHeight = $("#add_links").height();
        },
        resize: function (event, ui) {
            var addlinksNewHeight = Math.max(addlinksHeight + ui.size.height - ui.originalSize.height, addlinksMinHeight);
            $("#add_links").height(addlinksNewHeight);
        }
    }).draggable({ scroll: false });

	$('input[type=password].reveal-pass').map(function() {
	    var reveal_id;

	    $(this).wrap( "<div class=\"form-group has-feedback\"></div>" );
		var button = $("<button class='close form-control-feedback hidden' type='button' style='pointer-events: auto;'><span class='glyphicon glyphicon-eye-close' style='font-size: 11px;'></span></button>");
		reveal_id = Date.now();
		button.attr("data-reveal-pass-id", reveal_id);
		$(this).after(button);
		$(this).attr("data-reveal-pass-id", reveal_id);
		$(this).on('input', function () {
            var visible =  Boolean($(this).val());
            $(this).siblings('button[data-reveal-pass-id="' + $(this).attr("data-reveal-pass-id") + '"]').toggleClass('hidden', !visible);
        });
		button.mousedown(function(event) {
            event.preventDefault();
            $(this).find("span.glyphicon").removeClass('glyphicon-eye-close').addClass('glyphicon-eye-open');
            $(this).siblings('input[data-reveal-pass-id="' + $(this).attr("data-reveal-pass-id") + '"]').attr('type', 'text');
        }).mouseup(function(event) {
            event.preventDefault();
            $(this).find("span.glyphicon").removeClass('glyphicon-eye-open').addClass('glyphicon-eye-close');
            $(this).siblings('input[data-reveal-pass-id="' + $(this).attr("data-reveal-pass-id") + '"]').attr('type', 'password');
        }).click(function (event) {
            event.preventDefault();
        });
	});

    $('.btn, input[type="radio"]').focus(function() { this.blur(); });

    $("#add_form").submit(function(event) {
        event.preventDefault();
        var formData = new FormData(this);
        var $this = $(this);
        if ($this.find("#add_name").val() === "" && $this.find("#add_file").val() === "") {
            alert("{{_('Please Enter a package name.')}}");
            return false;
        } else {
            $.ajax({
                url: "{{url_for('json.add_package')}}",
                method: "POST",
                data: formData,
                processData: false,
                contentType: false,
                success: function() {
                    var queue = $this.find("#add_dest").val() === "1" ? "queue" : "collector";
                    var re = new RegExp("/" + queue + "/?$", "i");
                    if (window.location.toString().match(re)) {
                        window.location.reload();
                    }
                },
                error: function() {
                    indicateFail("{{_('Error occurred')}}");
                }
            });
            $("#add_box").modal('hide');
            return false;
        }
    });

    $(".action_add").click(function() {
        $("#add_form").trigger("reset");
    });

    $("#action_play").click(function() {
        $.get("{{url_for('api.rpc', func='unpause_server')}}", function () {
            $.ajax({
                method: "post",
                url: "{{url_for('json.status')}}",
                async: true,
                timeout: 3000,
                success: LoadJsonToContent
            });
        });
    });

    $("#action_cancel").click(function() {
        $.get("{{url_for('api.rpc', func='stop_all_downloads')}}");
    });

    $("#action_stop").click(function() {
        $.get("{{url_for('api.rpc', func='pause_server')}}", function () {
            $.ajax({
                method: "post",
                url: "{{url_for('json.status')}}",
                async: true,
                timeout: 3000,
                success: LoadJsonToContent
            });
        });
    });

    $(".cap_info").click(function() {
        load_captcha("get", "");
    });

    $("#cap_submit").click(function() {
        submit_captcha();
        // stop()??
    });

    $("#cap_box #cap_positional").click(submit_positional_captcha);

    if (thisScript.getAttribute('nopoll') !== "1") {
        $.ajax({
            method: "post",
            url: "{{url_for('json.status')}}",
            async: true,
            timeout: 3000,
            success: LoadJsonToContent
        });

        setInterval(function () {
            $.ajax({
                method: "post",
                url: "{{url_for('json.status')}}",
                async: true,
                timeout: 3000,
                success: LoadJsonToContent
            });
        }, 4000);
    }
});

function LoadJsonToContent(a) {
    var notification;
    $("#speed").text(humanFileSize(a.speed) + "/s");
    $("#actives").text(a.active);
    $("#actives_from").text(a.queue);
    $("#actives_total").text(a.total);
    var $cap_info = $(".cap_info");
    if (a.captcha) {
        var notificationVisible = ($cap_info.css("display") !== "none");
        if (!notificationVisible) {
            $cap_info.css('display','inline');
            mdtoast("{{_('New Captcha Request')}}", {position: "bottom center", type: "info", duration: 6000});
        }
        if (desktopNotifications && !document.hasFocus() && !notificationVisible) {
            notification = new Notification('pyLoad', {
                icon: "{{theme_static('img/favicon.ico')}}",
                body: "{{_('New Captcha Request')}}",
                tag: 'pyload_captcha'
            });
            notification.onclick = function (event) {
                event.preventDefault();
                parent.focus();
                window.focus();
                $("#action_cap")[0].click();
            };
            setTimeout(function() {
                notification.close()
            }, 8000);
        }
    } else {
        $cap_info.css('display', 'none');
    }
    if (a.download) {
        $("#time").text(" {{_('on')}}").css('background-color', '#5cb85c');
    } else {
        $("#time").text(" {{_('off')}}").css('background-color', "#d9534f");
    }
    if (a.reconnect) {
        $("#reconnect").text(" {{_('on')}}").css('background-color', "#5cb85c");
    } else {
        $("#reconnect").text(" {{_('off')}}").css('background-color', "#d9534f");
    }
    return null;
}

function set_captcha(a) {
    captcha_reset_default();

    params = JSON.parse(a.params);
    $("#cap_id").val(a.id);
    if (a.result_type === "textual") {
        $("#cap_textual_img").attr("src", params.src);
        $("#cap_submit").css("display", "inline");
        $("#cap_box #cap_title").text("");
        $("#cap_textual").css("display", "block");
        $("#cap_result").focus();
    } else if (a.result_type === "positional") {
        $("#cap_positional_img").attr("src", params.src);
        $("#cap_box #cap_title").text("{{_('Please click on the right captcha position.')}}");
        $("#cap_positional").css("display", "block");
    } else if (a.result_type === "interactive") {
        $("#cap_box #cap_title").text("");
        if(interactiveCaptchaHandlerInstance == null) {
            interactiveCaptchaHandlerInstance = new interactiveCaptchaHandler("cap_interactive_iframe", "cap_interactive_loading", submit_interactive_captcha);
        }
        if(params.url !== undefined && params.url.indexOf("http") === 0) {
            $("#cap_interactive").css("display", "block");
            interactiveCaptchaHandlerInstance.startInteraction(params.url, params);
        }
    } else if (a.result_type === "invisible") {
        $("#cap_box #cap_title").text("");
        if(interactiveCaptchaHandlerInstance == null) {
            interactiveCaptchaHandlerInstance = new interactiveCaptchaHandler("cap_interactive_iframe", "cap_invisible_loading", submit_interactive_captcha);
        }
        if(params.url !== undefined && params.url.indexOf("http") === 0) {
            $("#cap_interactive").css("display", "block");
            interactiveCaptchaHandlerInstance.startInteraction(params.url, params);
        }
    }
    return true;
}

function load_captcha(b, a) {
    $.ajax({
            url: "{{url_for('json.set_captcha')}}",
            async: true,
            method: b,
            data: a,
            success: function(c) {
                return (c.captcha ? set_captcha(c) : clear_captcha());
        }
    });
}

function captcha_reset_default() {
    $("#cap_textual").css("display", "none");
    $("#cap_textual_img").attr("src", "");
    $("#cap_positional").css("display", "none");
    $("#cap_positional_img").attr("src", "");
    $("#cap_interactive").css("display", "none");
    $("#cap_submit").css("display", "none");
    // $("#cap_box #cap_title").text("{{_('No Captchas to read.')}}");
    $("#cap_interactive_iframe").attr("src", "").css({display: "none", top: "", left: ""})
        .parent().css({height: "", width: ""});
    $("#cap_interactive_loading").css("display", "none");
    $("#cap_invisible_loading").css("display", "none");
    if(interactiveCaptchaHandlerInstance) {
        interactiveCaptchaHandlerInstance.clearEventlisteners();
        interactiveCaptchaHandlerInstance = null;
    }
    return true;
}

function clear_captcha() {
    captcha_reset_default();
    $('#cap_box').modal('hide');
    return true;
}

function submit_captcha() {
    var $cap_result = $("#cap_result");
    load_captcha("post", "cap_id=" + $("#cap_id").val() + "&cap_result=" + $cap_result.val());
    $cap_result.val("");
    return false;
}

function submit_positional_captcha(c) {
    var b, a, d;
    // b = c.target.getPosition();
    var x = (c.pageX - $(this).offset().left).toFixed(0);
    var y = (c.pageY - $(this).offset().top).toFixed(0);
    $("#cap_box #cap_result").val(x + ' , ' + y);
    return submit_captcha();
}

function submit_interactive_captcha(c) {
    if (c.constructor === {}.constructor)
        c = JSON.stringify(c);
    else if (c.constructor !== "".constructor)
        return;

    $("#cap_box #cap_result").val(c);
    return submit_captcha();
}

function interactiveCaptchaHandler(iframeId, loadingid, captchaResponseCallback) {
    this._iframeId = iframeId;
    this._loadingId = loadingid;
    this._captchaResponseCallback = captchaResponseCallback;
    this._active = false; // true: link grabbing is running, false: standby

    $("#" + this._loadingId).css("display", "block");
    $("#" + this._iframeId).on("load", this, this.iframeLoaded);

    // Register event listener for communication with iframe
    $(window).on('message', this, this.windowEventListener);
}

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
interactiveCaptchaHandler.prototype.windowEventListener = function(event) {
    var requestMessage;
    try {
        requestMessage = JSON.parse(event.originalEvent.data);
    } catch (e) {
        if (e instanceof SyntaxError) {
            return
        } else {
            console.error(e)
        }
    }
    var interactiveHandlerInstance = event.data;

    if(requestMessage.actionCode === interactiveHandlerInstance.actionCodes.submitResponse) {
        // We got the response! pass it to the callback function
        interactiveHandlerInstance._captchaResponseCallback(requestMessage.params.response);
        interactiveHandlerInstance.clearEventlisteners();

    } else if(requestMessage.actionCode === interactiveHandlerInstance.actionCodes.activated) {
        $("#" + interactiveHandlerInstance._loadingId).css("display", "none");
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
