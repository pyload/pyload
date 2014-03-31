{% autoescape true %}
  var root;

  root = this;

  window.addEvent("domready", function() {
    var id, item, user, _i, _len, _ref;
    root.passwordDialog = new MooDialog({
      destroyOnHide: false
    });
    root.passwordDialog.setContent($('password_box'));
    $("login_password_reset").addEvent("click", function(e) {
      return root.passwordDialog.close();
    });
    $("login_password_button").addEvent("click", function(e) {
      var form, newpw, newpw2;
      newpw = $("login_new_password").get("value");
      newpw2 = $("login_new_password2").get("value");
      if (newpw === newpw2) {
        form = $("password_form");
        form.set("send", {
          onSuccess: function(data) {
            return root.notify.alert("Success", {
              'className': 'success'
            });
          },
          onFailure: function(data) {
            return root.notify.alert("Error", {
              'className': 'error'
            });
          }
        });
        form.send();
        root.passwordDialog.close();
      } else {
        alert('{{_("Passwords did not match.")}}');
      }
      return e.stop();
    });
    _ref = $$(".change_password");
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      item = _ref[_i];
      id = item.get("id");
      user = id.split("|")[1];
      $("user_login").set("value", user);
      item.addEvent("click", function(e) {
        return root.passwordDialog.open();
      });
    }
    $('quit-pyload').addEvent("click", function(e) {
      new MooDialog.Confirm("{{_('You are really sure you want to quit pyLoad?')}}", function() {
        return new Request.JSON({
          url: "{{ '/api/kill'|url }}",
          method: 'get'
        }).send();
      }, function() {});
      return e.stop();
    });
    return $('restart-pyload').addEvent("click", function(e) {
      new MooDialog.Confirm("{{_('Are you sure you want to restart pyLoad?')}}", function() {
        return new Request.JSON({
          url: "{{ '/api/restart'|url }}",
          method: 'get',
          onSuccess: function(data) {
            return alert("{{_('pyLoad restarted')}}");
          }
        }).send();
      }, function() {});
      return e.stop();
    });
  });

{% endautoescape %}
