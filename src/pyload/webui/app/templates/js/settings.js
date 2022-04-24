/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */

{% autoescape true %}

document.addEvent('domready', function() {
  window.accountDialog = new MooDialog({destroyOnHide: false});
  window.accountDialog.setContent($('account_box'));
  {% if user.is_admin %}
    window.passwordDialog = new MooDialog({destroyOnHide: false});
    window.passwordDialog.setContent($('password_box'));
    window.userDialog = new MooDialog({destroyOnHide: false});
    window.userDialog.setContent($('user_box'));
  {% endif %}

  new TinyTab($$('#toptabs li a'), $$('#tabs-body > span'));

  $$('ul.nav').each(nav =>
    new MooDropMenu(nav, {
      onOpen(el) { return el.fade('in'); },
      onClose(el) { return el.fade('out'); },
      onInitialize(el) { return el.fade('hide').set('tween', {duration:500}); }
    }));

  return new SettingsUI();
});


class SettingsUI {
  constructor() {
    this.menu = $$("#general-menu li");
    this.menu.append($$("#plugin-menu li"));

    this.name = $("tabsback");
    this.general = $("general_form_content");
    this.plugin = $("plugin_form_content");

    for (let el of Array.from(this.menu)) { el.addEvent('click', this.menuClick.bind(this)); }

    $("core|submit").addEvent("click", this.configSubmit.bind(this));
    $("plugin|submit").addEvent("click", this.configSubmit.bind(this));

    $("account_add").addEvent("click", function(e) {
      window.accountDialog.open();
      return e.stop();
    });

    $("account_reset").addEvent("click", e => window.accountDialog.close());

    $("account_add_button").addEvent("click", this.addAccount.bind(this));
    $("account_submit").addEvent("click", this.submitAccounts.bind(this));

    {% if user.is_admin %}
      $("user_submit").addEvent("click", this.submitUsers.bind(this));
      $("login_password_reset").addEvent("click", e => window.passwordDialog.close());
      $("login_password_button").addEvent("click", function(e) {
          const newpw = $("login_new_password").get("value");
          const newpw2 = $("login_new_password2").get("value");

          if (newpw === newpw2) {
              const form = $("password_form");
              form.set("send", {
                  onSuccess(data) {
                      return window.notify.alert("Success", {
                          'className': 'success'
                      });
                  },
                  onFailure(data) {
                      return window.notify.alert("Error", {
                          'className': 'error'
                      });
                  }
              });

              form.send();

              window.passwordDialog.close();
          } else {
              alert('{{_("Passwords did not match")}}');
          }

          return e.stop();
      });

      $("new_user_reset").addEvent("click", e => window.userDialog.close());
      $("new_user_button").addEvent("click", function(e) {
          const $userName = $("new_user");
          if ($userName.get("value").trim() === "") {
              alert("{{_('Username must be filled out')}}");
          } else {
              $userName.set("value", $userName.get("value").trim());
              const passwd = $("new_password").get("value");
              const passwdConfirm = $("new_password2").get("value");
              if (passwd === passwdConfirm) {
                  const form = $("user_add_form");
                  form.set("send", {
                      onSuccess(data) {
                          window.notify.alert("Success", {
                              'className': 'success'
                          });
                          window.location.assign(window.location.href);
                      },
                      onFailure(data) {
                          window.notify.alert("Error", {
                              'className': 'error'
                          });
                          window.location.assign(window.location.href);
                      }
                  });

                  form.send();

                  window.userDialog.close();
              } else {
                  alert('{{_("Passwords did not match")}}');
              }

          }
          return e.stop();
      });

      $("user_add").addEvent("click", function(e) {
          window.userDialog.open();
          return e.stop();
      });

      for (let item of Array.from($$(".is_admin"))) {
          item.addEvent("change", function (e) {
              let userName = e.target.get("name").split("|")[0];
              let checked = e.target.checked;
              let permsList = $(userName + "|perms");
              permsList.set('disabled', checked);
              if (checked) {
                  let length = permsList.options.length;
                  for (i = length-1; i >= 0; i--) {
                      permsList.options[i].selected = false;
                  }
              }
          });
      }
      for (let item of Array.from($$(".change_password"))) {
          let id = item.get("id");
          let user = id.split("|")[1];
          item.addEvent("click",  function (u) {
              $("user_login").set("value", u);
              window.passwordDialog.open()
          }.bind(null, user));
      }

      $("new_role").addEvent("change", function (e) {
          let checked = this.checked;
          let permsList = $("new_perms");
          permsList.set('disabled', checked);
          if (checked) {
              let length = permsList.options.length;
              for (i = length-1; i >= 0; i--) {
                  permsList.options[i].selected = false;
              }
          }
      });

      $('quit-pyload').addEvent("click", function(e) {
          new MooDialog.Confirm("{{_('You are really sure you want to quit pyLoad?')}}", function() {
                  return new Request.JSON({
                      url: "{{url_for('api.rpc', func='kill')}}",
                      method: 'get'
                  }).send();
              }
              , function() {});
          return e.stop();
      });

      return $('restart-pyload').addEvent("click", function(e) {
          new MooDialog.Confirm("{{_('Are you sure you want to restart pyLoad?')}}", function() {
                  return new Request.JSON({
                      url: "{{url_for('api.rpc', func='restart')}}",
                      method: 'get',
                      onSuccess(data) { return alert("{{_('pyLoad restarted')}}"); }
                  }).send();
              }
              , function() {});
          return e.stop();
      });
    {% endif %}
  }


  menuClick(e) {
    const [category, section] = Array.from(e.target.get("id").split("|"));
    const name = e.target.get("text");


    let target = category === "core" ? this.general : this.plugin;
    target.dissolve();

    return new Request({
      "method" : "get",
      "url" : "{{url_for('json.load_config')}}",
      "data": {category: category, section: section},
      'onSuccess': data => {
        target.set("html", data);
        target.reveal();
        return this.name.set("text", name);
      }
    }).send();
  }


  configSubmit(e) {
    const category = e.target.get("id").split("|")[0];
    const form = $(category + '_form');

    form.set("send", {
      'method': "post",
      'url': "{{url_for('json.save_config')}}" + "?category="  + category,
      "onSuccess"() {
        return window.notify.alert('{{ _("Settings saved")}}', {
              'className': 'success'
            });
      },
      'onFailure'() {
        return window.notify.alert('{{ _("Error occured")}}', {
              'className': 'error'
            });
      }
    });
    form.send();
    return e.stop();
  }

  addAccount(e) {
    const form = $("add_account_form");
    form.set("send", {
      'method': "post",
      "onSuccess"() { return window.location.reload(); },
      'onFailure'() {
        return window.notify.alert('{{_("Error occured")}}', {
          'className': 'error'
          });
      }
      });

    form.send();
    return e.stop();
  }

  submitAccounts(e) {
    const form = $("account_form");
    form.set("send", {
       'method': "post",
       "onSuccess"() { return window.location.reload(); },
       'onFailure'() {
         return window.notify.alert('{{ _("Error occured") }}', {
               'className': 'error'
             });
       }
       });

    form.send();
    return e.stop();
  }

  submitUsers(e) {
    const form = $("user_form");
    form.set("send", {
       'method': "post",
       "onSuccess"() { return window.location.reload(); },
       'onFailure'() {
         return window.notify.alert('{{ _("Error occured") }}', {
               'className': 'error'
             });
       }
       });

    form.send();
    return e.stop();
  }
}

{% endautoescape %}
