{% autoescape true %}
  var SettingsUI, root;

  root = this;

  window.addEvent('domready', function() {
    root.accountDialog = new MooDialog({
      destroyOnHide: false
    });
    root.accountDialog.setContent($('account_box'));
    new TinyTab($$('#toptabs li a'), $$('#tabs-body > span'));
    $$('ul.nav').each(function(nav) {
      return new MooDropMenu(nav, {
        onOpen: function(el) {
          return el.fade('in');
        },
        onClose: function(el) {
          return el.fade('out');
        },
        onInitialize: function(el) {
          return el.fade('hide').set('tween', {
            duration: 500
          });
        }
      });
    });
    return new SettingsUI();
  });

  SettingsUI = (function() {
    function SettingsUI() {
      var el, _i, _len, _ref;
      this.menu = $$("#general-menu li");
      this.menu.append($$("#plugin-menu li"));
      this.name = $("tabsback");
      this.general = $("general_form_content");
      this.plugin = $("plugin_form_content");
      _ref = this.menu;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        el = _ref[_i];
        el.addEvent('click', this.menuClick.bind(this));
      }
      $("general|submit").addEvent("click", this.configSubmit.bind(this));
      $("plugin|submit").addEvent("click", this.configSubmit.bind(this));
      $("account_add").addEvent("click", function(e) {
        root.accountDialog.open();
        return e.stop();
      });
      $("account_reset").addEvent("click", function(e) {
        return root.accountDialog.close();
      });
      $("account_add_button").addEvent("click", this.addAccount.bind(this));
      $("account_submit").addEvent("click", this.submitAccounts.bind(this));
    }

    SettingsUI.prototype.menuClick = function(e) {
      var category, name, section, target, _ref;
      _ref = e.target.get("id").split("|"), category = _ref[0], section = _ref[1];
      name = e.target.get("text");
      target = category === "general" ? this.general : this.plugin;
      target.dissolve();
      return new Request({
        "method": "get",
        "url": "{{ '/json/load_config/'|url }}" + category + "/" + section,
        "onSuccess": (function(_this) {
          return function(data) {
            target.set("html", data);
            target.reveal();
            return _this.name.set("text", name);
          };
        })(this)
      }).send();
    };

    SettingsUI.prototype.configSubmit = function(e) {
      var category, form;
      category = e.target.get("id").split("|")[0];
      form = $("" + category + "_form");
      form.set("send", {
        "method": "post",
        "url": "{{ '/json/save_config/'|url }}" + category,
        "onSuccess": function() {
          return root.notify.alert('{{ _("Settings saved.")}}', {
            'className': 'success'
          });
        },
        "onFailure": function() {
          return root.notify.alert('{{ _("Error occured.")}}', {
            'className': 'error'
          });
        }
      });
      form.send();
      return e.stop();
    };

    SettingsUI.prototype.addAccount = function(e) {
      var form;
      form = $("add_account_form");
      form.set("send", {
        "method": "post",
        "onSuccess": function() {
          return window.location.reload();
        },
        "onFailure": function() {
          return root.notify.alert('{{_("Error occured.")}}', {
            'className': 'error'
          });
        }
      });
      form.send();
      return e.stop();
    };

    SettingsUI.prototype.submitAccounts = function(e) {
      var form;
      form = $("account_form");
      form.set("send", {
        "method": "post",
        "onSuccess": function() {
          return window.location.reload();
        },
        "onFailure": function() {
          return root.notify.alert('{{ _("Error occured.") }}', {
            'className': 'error'
          });
        }
      });
      form.send();
      return e.stop();
    };

    return SettingsUI;

  })();

{% endautoescape %}
