/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */

{% autoescape true %}

const root = this;

document.addEvent('domready', function() {
  root.accountDialog = new MooDialog({destroyOnHide: false});
  root.accountDialog.setContent($('account_box'));

  new TinyTab($$('#tabs li a'), $$('#tabs-body > span'));

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

    $("general|submit").addEvent("click", this.configSubmit.bind(this));
    $("plugin|submit").addEvent("click", this.configSubmit.bind(this));

    $("account_add").addEvent("click", function(e) {
      root.accountDialog.open();
      return e.stop();
    });

    $("account_reset").addEvent("click", e => root.accountDialog.close());

    $("account_add_button").addEvent("click", this.addAccount.bind(this));
    $("account_submit").addEvent("click", this.submitAccounts.bind(this));
  }


  menuClick(e) {
    const [category, section] = Array.from(e.target.get("id").split("|"));
    const name = e.target.get("text");


    const target = category === "general" ? this.general : this.plugin;
    target.dissolve();

    return new Request({
      "method" : "get",
      "url" : `/json/load_config/${category}/${section}`,
      'onSuccess': data => {
        target.set("html", data);
        target.reveal();
        return this.name.set("text", name);
      }
    }).send();
  }


  configSubmit(e) {
    const category = e.target.get("id").split("|")[0];
    const form = $(`${category}_form`);

    form.set("send", {
      'method': "post",
      'url': `/json/save_config/${category}`,
      "onSuccess"() {
        return root.notify.alert('{{ _("Settings saved")}}', {
              'className': 'success'
            });
      },
      'onFailure'() {
        return root.notify.alert('{{ _("Error occured")}}', {
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
        return root.notify.alert('{{_("Error occured")}}', {
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
         return root.notify.alert('{{ _("Error occured") }}', {
               'className': 'error'
             });
       }
       });

    form.send();
    return e.stop();
  }
}

{% endautoescape %}
