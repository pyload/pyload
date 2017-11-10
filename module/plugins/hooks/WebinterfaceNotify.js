{% autoescape true %}
var NotificationAvailable, NotificationData, NotificationFirstRequest, NotifyLoadJsonToContent, pyNotify, root;

root = this;

NotificationAvailable = false;

if ("{{notifications.activated.value}}".toLowerCase() === "true") {
  if (typeof Notification !== "undefined" && Notification !== null) {
    if (Notification.permission === "default") {
      Notification.requestPermission();
    }
    if (Notification.permission === "granted") {
      NotificationAvailable = true;
    }
  }
}

NotificationFirstRequest = true;

pyNotify = (function() {
  function pyNotify(arg) {
    var clickEvent, closeEvent, message, ref, tag, timeout;
    ref = arg != null ? arg : {}, tag = ref.tag, message = ref.message, timeout = ref.timeout, clickEvent = ref.clickEvent, closeEvent = ref.closeEvent;
    this.ongoing = false;
    this.object = null;
    this.last = 0;
    this.timer = null;
    this.tag = tag != null ? tag : '';
    this.message = message;
    this.timeout = parseInt(timeout);
    if (isNaN(this.timeout)) {
      this.timeout = 5;
    }
    this.timeout *= 1000;
    this.clickEvent = clickEvent != null ? clickEvent : null;
    this.closeEvent = closeEvent != null ? closeEvent : null;
    this.enabled = this.timeout < 0 ? false : true;
  }

  pyNotify.prototype.CreateNotification = function() {
    if (this.timeout < 0) {
      return;
    }
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.object = new Notification('pyLoad', {
      icon: '/media/plugins/WebinterfaceNotify/WebinterfaceNotifyLogo_static.png',
      body: this.message,
      tag: this.tag
    });
    if (this.clickEvent != null) {
      this.object.addEventListener('click', this.clickEvent);
    }
    if (this.closeEvent != null) {
      this.object.addEventListener('close', this.closeEvent);
    }
    this.ongoing = true;
    if (this.timeout > 0) {
      this.timer = setTimeout((function(me) {
        return me.DestroyNotification();
      }), this.timeout, this);
    }
  };

  pyNotify.prototype.DestroyNotification = function() {
    this.object.close();
    this.object = null;
    this.ongoing = false;
    this.timer = null;
  };

  return pyNotify;

})();

NotificationData = {
  captcha: new pyNotify({
    tag: 'captcha',
    message: '{{_("Captcha waiting")}}',
    clickEvent: (function() {
      return $("cap_info").click();
    }),
    timeout: '{{notifications.timeCaptcha.value}}'
  }),
  reconnecting: new pyNotify({
    tag: 'reconnect',
    message: '{{_("Reconnecting...")}}',
    timeout: '{{notifications.timeReconnecting.value}}'
  }),
  reconnectFinished: new pyNotify({
    tag: 'reconnect',
    message: '{{_("Reconnect complete!")}}',
    timeout: '{{notifications.timeReconnectFinished.value}}'
  }),
  fileFinished: new pyNotify({
    tag: 'file',
    message: '{{_("File finished!")}}',
    timeout: '{{notifications.timeFileFinished.value}}'
  }),
  fileFailed: new pyNotify({
    tag: 'file',
    message: '{{_("File failed!")}}',
    timeout: '{{notifications.timeFileFailed.value}}'
  }),
  packageFinished: new pyNotify({
    tag: 'package',
    message: '{{_("Package finished!")}}',
    timeout: '{{notifications.timePackageFinished.value}}'
  }),
  queueFinished: new pyNotify({
    tag: 'queue',
    message: '{{_("Queue finished!")}}',
    timeout: '{{notifications.timeQueueFinished.value}}'
  }),
  queueFailed: new pyNotify({
    tag: 'queue',
    message: '{{_("Queue failed!")}}',
    timeout: '{{notifications.timeQueueFinished.value}}'
  }),
  pluginsUpdated: new pyNotify({
    tag: 'plugins',
    message: '{{_("Plugins updated!")}}',
    timeout: '{{notifications.timePluginsUpdated.value}}'
  })
};

document.addEvent("domready", function() {
  return new Request.JSON({
    url: '/api/call?info=' + encodeURIComponent('{"plugin":"WebinterfaceNotify","func":"get_timestamps","arguments":None,"parseArguments":None}'),
    onSuccess: NotifyLoadJsonToContent,
    secure: false,
    async: true,
    initialDelay: 0,
    delay: 4000,
    limit: 3000
  }).startTimer();
});

NotifyLoadJsonToContent = function(data) {
  var event, nData, time;
  data = JSON.parse(data);
  if (NotificationAvailable) {
    for (event in data) {
      time = data[event];
      nData = NotificationData[event];
      if ((nData != null) && nData.last < time) {
        nData.last = time;
        if (!NotificationFirstRequest) {
          if (nData.enabled && !nData.ongoing) {
            nData.CreateNotification();
          }
        }
      }
      if ((nData != null) && time === 0) {
        nData.last = time;
        if (nData.ongoing) {
          nData.DestroyNotification();
        }
      }
    }
  }
  NotificationFirstRequest = false;
  return null;
};
{% endautoescape %}
