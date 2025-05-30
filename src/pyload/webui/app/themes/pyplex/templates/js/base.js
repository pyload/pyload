{% autoescape true %}

let desktopNotifications;
let interactiveCaptchaHandlerInstance = null;
const thisScript = document.currentScript;

const indicateLoad = () => $(".load-indicator").css('opacity', 1);

const indicateFinish = () => $(".load-indicator").css('opacity', 0);

const indicateSuccess = (message = "{{_('Success')}}") => {
  indicateFinish();
  mdtoast(`${message}.`, { position: "bottom center", type: "success", duration: 3000 });
};

const indicateFail = (message = "{{_('Failed')}}") => {
  indicateFinish();
  mdtoast(`${message}.`, { position: "bottom center", type: "error", duration: 4000 });
};

const humanFileSize = (f) => {
  const d = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"];
  const b = Math.log(f) / Math.log(1024);
  const e = Math.floor(b);
  const c = Math.pow(1024, e);
  return f === 0 ? "0 B" : `${Math.round(f * 100 / c) / 100} ${d[e]}`;
};

const parseUri = () => {
  const $add_links = $("#add_links");
  const b = $add_links.val();
  const g = new RegExp("(?:ht|f)tp(?:s?)://[a-zA-Z0-9-./?=_&%#:]+(?:[<| |\\\"|'|\\r|\\n|\\t]{1}|$)", "gi");
  const d = b.match(g);
  if (d === null) return $add_links.val("");

  let e = "";
  d.forEach(c => {
    e += c.replace(/[\s"'<>\n]/g, " \n");
  });
  return $add_links.val(e);
};

Array.prototype.remove = function(d, c) {
  const a = this.slice((c || d) + 1 || this.length);
  this.length = (d < 0 ? this.length + d : d);
  return this.push(...a);
};

const getScrollBarHeight = () => {
  const inner = document.createElement('p');
  inner.style.width = "200px";
  inner.style.height = "100%";

  const outer = document.createElement('div');
  outer.style.position = "absolute";
  outer.style.top = "0px";
  outer.style.left = "0px";
  outer.style.visibility = "hidden";
  outer.style.width = "150px";
  outer.style.height = "200px";
  outer.style.overflow = "hidden";
  outer.appendChild(inner);

  document.body.appendChild(outer);
  const w1 = inner.offsetHeight;
  outer.style.overflow = 'scroll';
  const w2 = inner.offsetHeight === w1 ? outer.clientHeight : inner.offsetHeight;

  document.body.removeChild(outer);

  return (w1 - w2);
};

const yesNoDialog = (question, callback) => {
  $('#modal_question').text(question);

  $('#okButton').off('click').on('click', () => {
    $('#yesno_box').modal('hide');
    callback(true);
  });

  $('#cancelButton').off('click').on('click', () => {
    $('#yesno_box').modal('hide');
    callback(false);
  });

  $('#yesno_box').modal('show');
};

$(() => {
  const $goto_top = $('#goto_top');
  const $stickyNav = $("#sticky-nav");
  let topbuttonVisible = $(window).scrollTop() > 100;

  $goto_top.toggleClass('hidden', !topbuttonVisible).affix({ offset: { top: 100 } });

  const stickynavlCss = (scrollTop) => {
    const $headPanel = $('#head-panel');
    const headpanelHeight = $headPanel.height();

    if (scrollTop <= headpanelHeight) {
      return { "display": "none" };
    } else if (scrollTop > headpanelHeight && scrollTop < headpanelHeight * 2) {
      return { "display": "block", "top": `${scrollTop - headpanelHeight * 2}px` };
    } else {
      return { "display": "block", "top": "0" };
    }
  };

  $stickyNav.css(stickynavlCss($(window).scrollTop()));

  $(window).scroll(() => {
    const scrollTop = $(this).scrollTop();
    const visible = Boolean(scrollTop > 100);

    if (topbuttonVisible !== visible) {
      $goto_top.toggleClass('hidden', !visible);
      topbuttonVisible = visible;
    }
    $stickyNav.css(stickynavlCss(scrollTop));
  });

  $goto_top.click(() => {
    $('html,body').animate({ scrollTop: 0 }, 'slow');
    return false;
  });

  desktopNotifications = false;
  if ("Notification" in window) {
    if (Notification.permission === 'granted') {
      desktopNotifications = true;
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(result => {
        desktopNotifications = (result === 'granted');
      });
    }
  }

  const addlinksMinHeight = getScrollBarHeight() + Math.round(parseFloat($("#add_links").css("line-height").replace('px', '')));
  let addlinksHeight;
  $("#modal-content").resizable({
    minHeight: 520 + addlinksMinHeight,
    minWidth: 310,
    start: (event, ui) => {
      addlinksHeight = $("#add_links").height();
    },
    resize: (event, ui) => {
      const addlinksNewHeight = Math.max(addlinksHeight + ui.size.height - ui.originalSize.height, addlinksMinHeight);
      $("#add_links").height(addlinksNewHeight);
    }
  }).draggable({ scroll: false });

  $('input[type=password].reveal-pass').map(function() {
    const reveal_id = Date.now();

    $(this).wrap("<div class=\"form-group has-feedback\"></div>");
    const button = $("<button class='close form-control-feedback hidden' type='button' style='pointer-events: auto;'><span class='glyphicon glyphicon-eye-close' style='font-size: 11px;'></span></button>");
    button.attr("data-reveal-pass-id", reveal_id);
    $(this).after(button);
    $(this).attr("data-reveal-pass-id", reveal_id);
    $(this).on('input', function() {
      const visible = Boolean($(this).val());
      $(this).siblings(`button[data-reveal-pass-id="${$(this).attr("data-reveal-pass-id")}"]`).toggleClass('hidden', !visible);
    });
    button.mousedown(event => {
      event.preventDefault();
      button.find("span.glyphicon").removeClass('glyphicon-eye-close').addClass('glyphicon-eye-open');
      $(this).siblings(`input[data-reveal-pass-id="${$(this).attr("data-reveal-pass-id")}"]`).attr('type', 'text');
    }).mouseup(event => {
      event.preventDefault();
      button.find("span.glyphicon").removeClass('glyphicon-eye-open').addClass('glyphicon-eye-close');
      $(this).siblings(`input[data-reveal-pass-id="${$(this).attr("data-reveal-pass-id")}"]`).attr('type', 'password');
    }).click(event => {
      event.preventDefault();
    });
  });

  $('.btn, input[type="radio"]').focus(function() { this.blur(); });

  $("#add_form").submit(function(event) {
    event.preventDefault();
    const formData = new FormData(this);
    const $this = $(this);
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
        success: () => {
          const queue = $this.find("#add_dest").val() === "1" ? "queue" : "collector";
          const re = new RegExp(`/${queue}/?$`, "i");
          if (window.location.toString().match(re)) {
            window.location.reload();
          }
        },
        error: () => {
          indicateFail("{{_('Error occurred')}}");
        }
      });
      $("#add_box").modal('hide');
      return false;
    }
  });

  $(".action_add").click(() => {
    $("#add_form").trigger("reset");
  });

  $("#action_play").click(() => {
    $.get("{{url_for('api.rpc', func='unpause_server')}}", () => {
      $.ajax({
        method: "post",
        url: "{{url_for('json.status')}}",
        async: true,
        timeout: 3000,
        success: LoadJsonToContent
      });
    });
  });

  $("#action_cancel").click(() => {
    yesNoDialog("{{_('Are you sure you want to abort all downloads?')}}", (answer) => {
      if (answer) {
        $.get("{{url_for('api.rpc', func='stop_all_downloads')}}");
      }
    });
  });

  $("#action_stop").click(() => {
    $.get("{{url_for('api.rpc', func='pause_server')}}", () => {
      $.ajax({
        method: "post",
        url: "{{url_for('json.status')}}",
        async: true,
        timeout: 3000,
        success: LoadJsonToContent
      });
    });
  });

  $("#toggle_queue").click(() => {
    $.get("{{url_for('api.rpc', func='toggle_pause')}}", () => {
      $.ajax({
        method: "post",
        url: "{{url_for('json.status')}}",
        async: true,
        timeout: 3000,
        success: LoadJsonToContent
      });
    });
  });

  $("#toggle_proxy").click(() => {
    $.get("{{url_for('api.rpc', func='toggle_proxy')}}", () => {
      $.ajax({
        method: "post",
        url: "{{url_for('json.status')}}",
        async: true,
        timeout: 3000,
        success: LoadJsonToContent
      });
    });
  });

  $("#toggle_reconnect").click(() => {
    $.get("{{url_for('api.rpc', func='toggle_reconnect')}}", () => {
      $.ajax({
        method: "post",
        url: "{{url_for('json.status')}}",
        async: true,
        timeout: 3000,
        success: LoadJsonToContent
      });
    });
  });

  $(".cap_info").click(() => {
    load_captcha("get", "");
  });

  $("#cap_submit").click(() => {
    submit_captcha();
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

    setInterval(() => {
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

const LoadJsonToContent = (a) => {
  $("#speed").text(`${humanFileSize(a.speed)}/s`);
  $("#actives").text(a.active);
  $("#actives_from").text(a.queue);
  $("#actives_total").text(a.total);
  const $cap_info = $(".cap_info");
  if (a.captcha) {
    const notificationVisible = ($cap_info.css("display") !== "none");
    if (!notificationVisible) {
      $cap_info.css('display', 'inline');
      mdtoast("{{_('New Captcha Request')}}", { position: "bottom center", type: "info", duration: 6000 });
    }
    if (desktopNotifications && !document.hasFocus() && !notificationVisible) {
      const notification = new Notification('pyLoad', {
        icon: "{{theme_static('img/favicon.ico')}}",
        body: "{{_('New Captcha Request')}}",
        tag: 'pyload_captcha'
      });
      notification.onclick = (event) => {
        event.preventDefault();
        parent.focus();
        window.focus();
        $("#action_cap")[0].click();
      };
      setTimeout(() => {
        notification.close();
      }, 8000);
    }
  } else {
    $cap_info.css('display', 'none');
  }
  $("#time").text(a.download ? " {{_('on')}}" : " {{_('off')}}").css('background-color', a.download ? '#5cb85c' : "#d9534f");
  $("#proxy").text(a.proxy ? " {{_('on')}}" : " {{_('off')}}").css('background-color', a.proxy ? "#5cb85c" : "#d9534f");
  $("#reconnect").text(a.reconnect ? " {{_('on')}}" : " {{_('off')}}").css('background-color', a.reconnect ? "#5cb85c" : "#d9534f");
  return null;
};

const set_captcha = (catchaData) => {
  captcha_reset_default();

  $("#cap_id").val(catchaData.id);
  if (catchaData.result_type === "textual") {
    $("#cap_textual_img").attr("src", catchaData.params.src);
    $("#cap_submit").css("display", "inline");
    $("#cap_box #cap_title").text("");
    $("#cap_textual").css("display", "block");
    $("#cap_result").focus();
  } else if (catchaData.result_type === "positional") {
    $("#cap_positional_img").attr("src", catchaData.params.src);
    $("#cap_box #cap_title").text("{{_('Please click on the right captcha position.')}}");
    $("#cap_positional").css("display", "block");
  } else if (catchaData.result_type === "interactive") {
    $("#cap_box #cap_title").text("");
    if (interactiveCaptchaHandlerInstance == null) {
      interactiveCaptchaHandlerInstance = new interactiveCaptchaHandler("cap_interactive_iframe", "cap_interactive_loading", submit_interactive_captcha);
    }
    if (catchaData.params.url !== undefined && catchaData.params.url.indexOf("http") === 0) {
      $("#cap_interactive").css("display", "block");
      interactiveCaptchaHandlerInstance.startInteraction(catchaData.params.url, catchaData.params);
    }
  } else if (catchaData.result_type === "invisible") {
    $("#cap_box #cap_title").text("");
    if (interactiveCaptchaHandlerInstance == null) {
      interactiveCaptchaHandlerInstance = new interactiveCaptchaHandler("cap_interactive_iframe", "cap_invisible_loading", submit_interactive_captcha);
    }
    if (catchaData.params.url !== undefined && catchaData.params.url.indexOf("http") === 0) {
      $("#cap_interactive").css("display", "block");
      interactiveCaptchaHandlerInstance.startInteraction(catchaData.params.url, catchaData.params);
    }
  }
  return true;
};

const load_captcha = (b, a) => {
  $.ajax({
    url: "{{url_for('json.set_captcha')}}",
    async: true,
    method: b,
    data: a,
    success: (c) => (c.captcha ? set_captcha(c) : clear_captcha())
  });
};

const captcha_reset_default = () => {
  $("#cap_textual").css("display", "none");
  $("#cap_textual_img").attr("src", "");
  $("#cap_positional").css("display", "none");
  $("#cap_positional_img").attr("src", "");
  $("#cap_interactive").css("display", "none");
  $("#cap_submit").css("display", "none");
  $("#cap_interactive_iframe").attr("src", "").css({ display: "none", top: "", left: "" })
    .parent().css({ height: "", width: "" });
  $("#cap_interactive_loading").css("display", "none");
  $("#cap_invisible_loading").css("display", "none");
  if (interactiveCaptchaHandlerInstance) {
    interactiveCaptchaHandlerInstance.clearEventlisteners();
    interactiveCaptchaHandlerInstance = null;
  }
  return true;
};

const clear_captcha = () => {
  captcha_reset_default();
  $('#cap_box').modal('hide');
  return true;
};

const submit_captcha = () => {
  const $cap_result = $("#cap_result");
  load_captcha("post", `cap_id=${$("#cap_id").val()}&cap_result=${$cap_result.val()}`);
  $cap_result.val("");
  return false;
};

const submit_positional_captcha = (c) => {
  const x = (c.pageX - $(this).offset().left).toFixed(0);
  const y = (c.pageY - $(this).offset().top).toFixed(0);
  $("#cap_box #cap_result").val(`${x} , ${y}`);
  return submit_captcha();
};

const submit_interactive_captcha = (c) => {
  if (c.constructor === {}.constructor)
    c = JSON.stringify(c);
  else if (c.constructor !== "".constructor)
    return;

  $("#cap_box #cap_result").val(c);
  return submit_captcha();
};

function interactiveCaptchaHandler(iframeId, loadingid, captchaResponseCallback) {
  this._iframeId = iframeId;
  this._loadingId = loadingid;
  this._captchaResponseCallback = captchaResponseCallback;
  this._active = false;

  $(`#${this._loadingId}`).css("display", "block");
  $(`#${this._iframeId}`).on("load", this, this.iframeLoaded);

  $(window).on('message', this, this.windowEventListener);
}

interactiveCaptchaHandler.prototype.iframeLoaded = function(e) {
  const interactiveHandlerInstance = e.data;
  if (interactiveHandlerInstance._active) {
    const requestMessage = {
      actionCode: interactiveHandlerInstance.actionCodes.activate,
      params: interactiveHandlerInstance._params
    };
    $(`#${interactiveHandlerInstance._iframeId}`).get(0).contentWindow.postMessage(JSON.stringify(requestMessage), "*");
  }
};

interactiveCaptchaHandler.prototype.startInteraction = function(url, params) {
  this._active = true;
  this._params = params;
  $(`#${this._iframeId}`).attr("src", url);
};

interactiveCaptchaHandler.prototype.windowEventListener = function(event) {
  let requestMessage;
  try {
    requestMessage = JSON.parse(event.originalEvent.data);
  } catch (e) {
    if (e instanceof SyntaxError) {
      return;
    } else {
      console.error(e);
    }
  }
  const interactiveHandlerInstance = event.data;

  if (requestMessage.actionCode === interactiveHandlerInstance.actionCodes.submitResponse) {
    interactiveHandlerInstance._captchaResponseCallback(requestMessage.params.response);
    interactiveHandlerInstance.clearEventlisteners();
  } else if (requestMessage.actionCode === interactiveHandlerInstance.actionCodes.activated) {
    $(`#${interactiveHandlerInstance._loadingId}`).css("display", "none");
    $(`#${interactiveHandlerInstance._iframeId}`).css("display", "block");
  } else if (requestMessage.actionCode === interactiveHandlerInstance.actionCodes.size) {
    const $iframe = $(`#${interactiveHandlerInstance._iframeId}`);
    const width = requestMessage.params.rect.right - requestMessage.params.rect.left;
    const height = requestMessage.params.rect.bottom - requestMessage.params.rect.top;
    $iframe.css({ top: -requestMessage.params.rect.top + "px", left: -requestMessage.params.rect.left + "px" })
      .parent().width(width).height(height);
  }
};

interactiveCaptchaHandler.prototype.clearEventlisteners = function() {
  this._active = false;
  $(`#${this._iframeId}`).off("load", this.iframeLoaded);
  $(window).off('message', this.windowEventListener);
};

interactiveCaptchaHandler.prototype.actionCodes = {
  activate: "pyloadActivateInteractive",
  activated: "pyloadActivatedInteractive",
  size: "pyloadIframeSize",
  submitResponse: "pyloadSubmitResponse"
};

{% endautoescape %}
