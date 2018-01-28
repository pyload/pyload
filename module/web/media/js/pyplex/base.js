{% autoescape true %}
var desktopNotifications;
//root = this;

function indicateLoad() {
    $("#load-indicator").css('opacity',1);
}

function indicateFinish() {
    $("#load-indicator").css('opacity',0);
}

function indicateSuccess(message) {
   if(message === undefined) {
      message = "{{_('Success')}}";
   }

    indicateFinish();
    $.bootstrapPurr(message + '.', {
        offset: {amount: 5},
        type: 'success',
        align: 'center',
        draggable: false,
        allowDismiss: false
    });
}

function indicateFail(message) {
   if(message === undefined) {
      message = "{{_('Failed')}}";
   }

    indicateFinish();
    $.bootstrapPurr(message + '.', {
        offset: {amount: 5},
        type: 'danger',
        align: 'center',
        draggable: false,
        allowDismiss: false
    });
}

function humanFileSize(f) {
    var c, d, e, b;
    d = new Array("B", "KiB", "MiB", "GiB", "TiB", "PiB");
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
    b = $("#add_links").val();
    g = new RegExp("(?:ht|f)tp(?:s?)://[a-zA-Z0-9-./?=_&%#:]+(?:[<| |\\\"|'|\\r|\\n|\\t]{1}|$)", "gi");
    d = b.match(g);
    if (d === null) {
        return $("#add_links").val("");
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
    return $("#add_links").val(e);
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
    if (w1 == w2) w2 = outer.clientHeight;

    document.body.removeChild(outer);

    return (w1 - w2);
}

$(function() {
    var topbuttonVisible = $(window).scrollTop() > 100;
    $('#goto_top').toggleClass('hidden', !topbuttonVisible).affix({offset: {top:100}});

    $(window).scroll(function() {
        var visible = Boolean($(this).scrollTop() > 100);
        if (topbuttonVisible !== visible) {
            $('#goto_top').toggleClass('hidden', !visible);
            topbuttonVisible = visible;
        }
    });

    $("#goto_top").click(function () {
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
	    var revealid;

	    $(this).wrap( "<div class=\"form-group has-feedback\"></div>" );
		var button = $("<button class='close form-control-feedback hidden' type='button' style='pointer-events: auto;'><span class='glyphicon glyphicon-eye-close' style='font-size: 11px;'></span></button>");
		revealid = Date.now();
		button.attr("data-reveal-pass-id", revealid);
		$(this).after(button);
		$(this).attr("data-reveal-pass-id", revealid);
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
        if ($("#add_name").value === "" && $("#add_file").value === "") {
            alert("{{_('Please Enter a package name.')}}");
            return false;
        } else {
            var form = new FormData(this);
            $.ajax({
                    url: "{{'/json/add_package'|url}}",
                    method: "POST",
                    data: form,
                    processData: false,
                    contentType: false
            });
            $('#add_box').modal('hide');
            var queue = form.get("add_dest") === "1" ? "queue" : "collector";
            var re = new RegExp("/" + queue + "/?$", "i");
            if (window.location.toString().match(re)) {
                window.location.reload();
            }
            return false;
        }
    });

    $("#action_add").click(function() {
        $("#add_form").trigger("reset");
    });

    $("#action_play").click(function() {
        $.get("{{'/api/unpauseServer'|url}}", function () {
            $.ajax({
                method: "post",
                url: "{{'/json/status'|url}}",
                async: true,
                timeout: 3000,
                success: LoadJsonToContent
            });
        });
    });

    $("#action_cancel").click(function() {
        $.get("{{'/api/stopAllDownloads'|url}}");
    });

    $("#action_stop").click(function() {
        $.get("{{'/api/pauseServer'|url}}", function () {
            $.ajax({
                method: "post",
                url: "{{'/json/status'|url}}",
                async: true,
                timeout: 3000,
                success: LoadJsonToContent
            });
        });
    });

    $("#cap_info").click(function() {
        load_captcha("get", "");
    });

    $("#cap_submit").click(function() {
            submit_captcha();
            // stop()??
    });

    $("#cap_box #cap_positional").click(on_captcha_click);
    $.ajax({
        method:"post",
        url: "{{'/json/status'|url}}",
        async: true,
        timeout: 3000,
        success:LoadJsonToContent
    });

    setInterval(function() {
        $.ajax({
            method:"post",
            url: "{{'/json/status'|url}}",
            async: true,
            timeout: 3000,
            success:LoadJsonToContent
        });
    }, 4000);
});

function LoadJsonToContent(a) {
    var notification;
    $("#speed").text(humanFileSize(a.speed) + "/s");
    $("#aktiv").text(a.active);
    $("#aktiv_from").text(a.queue);
    $("#aktiv_total").text(a.total);
    if (a.captcha) {
        var notificationVisible = ($("#cap_info").css("display") !== "none");
        if (!notificationVisible) {
            $("#cap_info").css('display','inline');
            $.bootstrapPurr("{{_('New Captcha Request')}}",{
                offset: { amount: 10},
                align: 'center',
                draggable: false,
                allowDismiss: false
            });
        }
        if (desktopNotifications && !document.hasFocus() && !notificationVisible) {
            notification = new Notification('pyLoad', {
                icon: "{{'/favicon.ico'|url}}",
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
        $("#cap_info").css('display','none');
    }
    if (a.download) {
        $("#time").text(" {{_('on')}}");
        $("#time").css('background-color','#5cb85c');
    } else {
        $("#time").text(" {{_('off')}}");
        $("#time").css('background-color',"#d9534f");
    }
    if (a.reconnect) {
        $("#reconnect").text(" {{_('on')}}");
        $("#reconnect").css('background-color',"#5cb85c");
    } else {
        $("#reconnect").text(" {{_('off')}}");
        $("#reconnect").css('background-color',"#d9534f");
    }
    return null
}

function set_captcha(a) {
    $("#cap_id").val(a.id);
    if (a.result_type === "textual") {
        $("#cap_textual_img").attr("src", a.src);
        $("#cap_submit").css("display", "inline");
        $("#cap_box #cap_title").text('');
        $("#cap_textual").css("display", "block");
        return $("#cap_positional").css("display", "none");
    } else {
        if (a.result_type === "positional") {
            $("#cap_positional_img").attr("src", a.src);
            $("#cap_box #cap_title").text("{{_('Please click on the right captcha position.')}}");
            $("#cap_submit").css("display", "none");
            return $("#cap_textual").css("display", "none");
        }
    }
}

function load_captcha(b, a) {
    $.ajax({
            url: "{{'/json/set_captcha'|url}}",
            async: true,
            method: b,
            data: a,
            success: function(c) {
                set_captcha(c);
                return (c.captcha ? void 0 : clear_captcha());
        }
    });
}

function clear_captcha() {
    $("#cap_textual").css("display", "none");
    $("#cap_textual_img").attr("src", "");
    $("#cap_positional").css("display", "none");
    $("#cap_positional_img").attr("src", "");
    $("#cap_submit").css("display", "none");
    $("#cap_box #cap_title").text("{{_('No Captchas to read.')}}");
    $('#cap_box').modal('toggle');
}

function submit_captcha() {
    load_captcha("post", "cap_id=" + $("#cap_id").val() + "&cap_result=" + $("#cap_result").val());
    $("#cap_result").val("");
    return false;
}

function on_captcha_click(c) {
    var b, a, d;
    // b = c.target.getPosition();
    var x = (c.pageX - $(this).offset().left).toFixed(0);
    var y = (c.pageY - $(this).offset().top).toFixed(0);
    $("#cap_box #cap_result").val(x + ' , ' + y);
    return submit_captcha();
}

{% endautoescape %}