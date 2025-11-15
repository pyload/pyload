{% autoescape true %}
// Set up CSRF token for all AJAX requests
const getCsrfToken = () => document.querySelector('meta[name="csrf-token"]').getAttribute('content');

// Add CSRF token to all jQuery AJAX requests
$.ajaxSetup({
  beforeSend: function (xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
    }
  }
});

class NotificationHandler {
  constructor() {
    this.enabled = false;
    this.checkPermission();
  }

  checkPermission() {
    if ("Notification" in window) {
      if (Notification.permission === 'granted') {
        this.enabled = true;
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(result => {
          this.enabled = (result === 'granted');
        });
      }
    }
  }

  showNotification(title, options, callback) {
    if (this.enabled) {
      const notification = new Notification(title, options);
      if (callback) {
        notification.onclick = callback;
      }
      setTimeout(() => {
        notification.close();
      }, options.duration || 8000);
      return notification;
    }
    return null;
  }
}

let notificationHandler = new NotificationHandler();

class CaptchaHandler {
  constructor() {
    this._interactiveCaptchaActive = false;
  }

  iframeLoaded = (event) => {
    const interactionData = event.data;
    if (this._interactiveCaptchaActive) {
      const requestMessage = {
        actionCode: this.actionCodes.activate,
        params: interactionData.params
      };
      $("#cap_interactive_iframe").get(0).contentWindow.postMessage(JSON.stringify(requestMessage), "*");
    }
  }

  windowEventListener = (event) => {
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
    const interactionData = event.data;
    if (requestMessage.actionCode === this.actionCodes.submitResponse) {
      this.submitInteractiveCaptcha(requestMessage.params.response);
      this.clearEventlisteners();
    } else if (requestMessage.actionCode === this.actionCodes.activated) {
      $(`#${interactionData.infoId}`).css("display", "none");
      $("#cap_interactive_iframe").css("display", "block");
    } else if (requestMessage.actionCode === this.actionCodes.size) {
      const $iframe = $("#cap_interactive_iframe");
      const width = requestMessage.params.rect.right - requestMessage.params.rect.left;
      const height = requestMessage.params.rect.bottom - requestMessage.params.rect.top;
      $iframe.css({ top: -requestMessage.params.rect.top + "px", left: -requestMessage.params.rect.left + "px" })
        .parent().width(width).height(height);
    }
  }

  clearEventlisteners = () => {
    this._interactiveCaptchaActive = false;
    $("#cap_interactive_iframe").off("load", this.iframeLoaded);
    $(window).off('message', this.windowEventListener);
  }

  startInteraction = (interactionData) => {
    $(`#${interactionData.infoId}`).css("display", "block");
    $("#cap_interactive_iframe").on("load", interactionData, this.iframeLoaded);
    $(window).on('message', interactionData, this.windowEventListener);
    if (interactionData.params.url !== undefined && interactionData.params.url.indexOf("http") === 0) {
      $("#cap_interactive").css("display", "block");
      this._interactiveCaptchaActive = true;
      $("#cap_interactive_iframe").attr("src", interactionData.params.url);
    }
  }

  actionCodes = {
    activate: "pyloadActivateInteractive",
    activated: "pyloadActivatedInteractive",
    size: "pyloadIframeSize",
    submitResponse: "pyloadSubmitResponse"
  }

  setCaptcha = (captchaData) => {
    this.captchaResetDefault();

    $("#cap_id").val(captchaData.id);
    if (captchaData.result_type === "textual") {
      $("#cap_textual_img").attr("src", captchaData.params.src);
      $("#cap_submit").css("display", "inline");
      $("#cap_box #cap_title").text("");
      $("#cap_textual").css("display", "block");
      $("#cap_result").focus();
    } else if (captchaData.result_type === "positional") {
      $("#cap_positional_img").attr("src", captchaData.params.src);
      $("#cap_box #cap_title").text("{{_('Please click on the right captcha position.')}}");
      $("#cap_positional").css("display", "block");
    } else if (captchaData.result_type === "interactive" || captchaData.result_type === "invisible") {
      $("#cap_box #cap_title").text("");
      const infoId = captchaData.result_type === "interactive" ? "cap_interactive_loading" : "cap_invisible_loading"
      const interactionData = {
        infoId: infoId,
        params: captchaData.params
      }
      this.startInteraction(interactionData);
    }
    return true;
  }

  loadCaptcha = (method, data) => {
    $.ajax({
      url: "{{url_for('json.set_captcha')}}",
      async: true,
      method: method,
      data: data,
      success: (response) => (response.captcha ? this.setCaptcha(response) : this.clearCaptcha())
    });
  }

  captchaResetDefault = () => {
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
    this.clearEventlisteners();
    return true;
  }

  clearCaptcha = () => {
    this.captchaResetDefault();
    $('#cap_box').modal('hide');
    return true;
  }

  submitCaptcha = () => {
    const $cap_result = $("#cap_result");
    this.loadCaptcha("post", `cap_id=${$("#cap_id").val()}&cap_result=${$cap_result.val()}`);
    $cap_result.val("");
    return false;
  }

  submitPositionalCaptcha = (event) => {
    const x = (event.pageX - $(event.target).offset().left).toFixed(0);
    const y = (event.pageY - $(event.target).offset().top).toFixed(0);
    $("#cap_box #cap_result").val(`${x} , ${y}`);
    return this.submitCaptcha();
  }

  submitInteractiveCaptcha = (data) => {
    if (data.constructor === {}.constructor)
      data = JSON.stringify(data);
    else if (data.constructor !== "".constructor)
      return;

    $("#cap_box #cap_result").val(data);
    return this.submitCaptcha();
  }
}

var captchaHandler = new CaptchaHandler();
const thisScript = document.currentScript;

class UIHandler {
  constructor() {
    this.topbuttonVisible = $(window).scrollTop() > 100;
  }

  initUI() {
    const $goto_top = $('#goto_top');
    const $stickyNav = $("#sticky-nav");
    const navHeight = $('#head-panel').height();

    $goto_top.toggleClass('hidden', !this.topbuttonVisible).affix({ offset: { top: 100 } });
    const navCss = this.stickynavlCss($(window).scrollTop(), navHeight);
    const modalTop = navHeight + parseFloat((navCss.top || `${-navHeight}`.replace('px', ''))) + 5;
    $(".modal .modal-dialog").css({top: `${modalTop}px`});
    $stickyNav.css(navCss);

    const addlinksMinHeight = getScrollBarHeight() + Math.round(parseFloat($("#add_links").css("line-height").replace('px', '')));
    let addlinksHeight;
    $("#add_box .modal-content").resizable({
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

    $(window).scroll(() => this.handleScroll($goto_top, $stickyNav, navHeight));
    $goto_top.click(() => this.scrollToTop());
    this.initPasswordReveal();
    this.initButtonHandlers();
  }

  handleScroll($goto_top, $stickyNav, navHeight) {
    const scrollTop = $(window).scrollTop();
    const visible = Boolean(scrollTop > 100);

    if (this.topbuttonVisible !== visible) {
      $goto_top.toggleClass('hidden', !visible);
      this.topbuttonVisible = visible;
    }
    const navCss = this.stickynavlCss(scrollTop, navHeight);
    const modalTop = navHeight + parseFloat((navCss.top || `${-navHeight}`).replace('px', '')) + 5;
    $(".modal .modal-dialog").css({top: `${modalTop}px`});
    $stickyNav.css(navCss);
  }

  stickynavlCss(scrollTop, navHeight) {
    if (scrollTop <= navHeight) {
      return { "display": "none" };
    } else if (scrollTop > navHeight && scrollTop < navHeight * 2) {
      return { "display": "block", "top": `${scrollTop - navHeight * 2}px` };
    } else {
      return { "display": "block", "top": "0" };
    }
  }

  initPasswordReveal() {
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
  }

  initButtonHandlers() {
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
      $.post("{{url_for('api.rpc', func='unpause_server')}}", () => {
        $.ajax({
          method: "post",
          url: "{{url_for('json.status')}}",
          async: true,
          timeout: 3000,
          success: loadJsonToContent
        });
      });
    });

    $("#action_cancel").click(() => {
      this.yesNoDialog("{{_('Are you sure you want to abort all downloads?')}}", (answer) => {
        if (answer) {
          $.post("{{url_for('api.rpc', func='stop_all_downloads')}}");
        }
      });
    });

    $("#action_stop").click(() => {
      $.post("{{url_for('api.rpc', func='pause_server')}}", () => {
        $.ajax({
          method: "post",
          url: "{{url_for('json.status')}}",
          async: true,
          timeout: 3000,
          success: loadJsonToContent
        });
      });
    });

    $("#toggle_queue").click(() => {
      $.post("{{url_for('api.rpc', func='toggle_pause')}}", () => {
        $.ajax({
          method: "post",
          url: "{{url_for('json.status')}}",
          async: true,
          timeout: 3000,
          success: loadJsonToContent
        });
      });
    });

    $("#toggle_proxy").click(() => {
      $.post("{{url_for('api.rpc', func='toggle_proxy')}}", () => {
        $.ajax({
          method: "post",
          url: "{{url_for('json.status')}}",
          async: true,
          timeout: 3000,
          success: loadJsonToContent
        });
      });
    });

    $("#toggle_reconnect").click(() => {
      $.post("{{url_for('api.rpc', func='toggle_reconnect')}}", () => {
        $.ajax({
          method: "post",
          url: "{{url_for('json.status')}}",
          async: true,
          timeout: 3000,
          success: loadJsonToContent
        });
      });
    });

    $(".cap_info").click(() => {
      captchaHandler.loadCaptcha("get", "");
    });

    $("#cap_submit").click(() => {
      captchaHandler.submitCaptcha();
    });

    $("#cap_box #cap_positional").click(captchaHandler.submitPositionalCaptcha);
  }

  scrollToTop() {
    $('html,body').animate({ scrollTop: 0 }, 'slow');
    return false;
  }

  indicateLoad() {
    $(".load-indicator").css('opacity', 1);
  }

  indicateFinish() {
    $(".load-indicator").css('opacity', 0);
  }

  indicateSuccess(message = "{{_('Success')}}", duration = 3000) {
    this.indicateFinish();
    mdtoast(`${message}.`, { position: "bottom center", type: "success", duration: duration });
  }

  indicateFail(message = "{{_('Failed')}}", duration = 4000) {
    this.indicateFinish();
    mdtoast(`${message}.`, { position: "bottom center", type: "error", duration: duration });
  }

  indicateInfo(message, duration = 6000) {
    this.indicateFinish();
    mdtoast(`${message}.`, { position: "bottom center", type: "info", duration: duration });
  }

  yesNoDialog(question, callback) {
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
  }
}

var uiHandler = new UIHandler();

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

Array.prototype.remove = function(from, to) {
    let left;
    const rest = this.slice(((to || from) + 1) || this.length);
    this.length = (left = from < 0) != null ? left : this.length + {from};
    if (this.length === 0) { return []; }
    return this.push.apply(this, rest);
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

$(() => {
  uiHandler.initUI()

  if (thisScript.getAttribute('nopoll') !== "1") {
    $.ajax({
      method: "post",
      url: "{{url_for('json.status')}}",
      async: true,
      timeout: 3000,
      success: loadJsonToContent
    });

    const statusInterval = setInterval(() => {
      $.ajax({
        method: "post",
        url: "{{url_for('json.status')}}",
        async: true,
        timeout: 3000,
        success: loadJsonToContent,
        error: (xhr) => {
          if (xhr.status === 400) {
            clearInterval(statusInterval);
            uiHandler.indicateInfo("{{_('Status updates stopped due to authentication error,<br>please refresh the page')}}", 0);
          }
        }
      });
    }, 4000);
  }
});

const loadJsonToContent = (a) => {
  $("#speed").text(`${humanFileSize(a.speed)}/s`);
  $("#actives").text(a.active);
  $("#actives_from").text(a.queue);
  $("#actives_total").text(a.total);
  const $cap_info = $(".cap_info");
  if (a.captcha) {
    const notificationVisible = ($cap_info.css("display") !== "none");
    if (!notificationVisible) {
      $cap_info.css('display', 'inline');
      uiHandler.indicateInfo("{{_('New Captcha Request')}}");
    }
    if (notificationHandler.enabled && !document.hasFocus() && !notificationVisible) {
      const notification = notificationHandler.showNotification('pyLoad', {
        icon: "{{theme_static('img/favicon.ico')}}",
        body: "{{_('New Captcha Request')}}",
        tag: 'pyload_captcha'
      }, (event) => {
        event.preventDefault();
        parent.focus();
        window.focus();
        $("#action_cap")[0].click();
      });
    }
  } else {
    $cap_info.css('display', 'none');
  }
  $("#time").text(a.download ? " {{_('on')}}" : " {{_('off')}}").css('background-color', a.download ? '#5cb85c' : "#d9534f");
  $("#proxy").text(a.proxy ? " {{_('on')}}" : " {{_('off')}}").css('background-color', a.proxy ? "#5cb85c" : "#d9534f");
  $("#reconnect").text(a.reconnect ? " {{_('on')}}" : " {{_('off')}}").css('background-color', a.reconnect ? "#5cb85c" : "#d9534f");
  return null;
};

{% endautoescape %}
