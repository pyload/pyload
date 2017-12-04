root = this

window.addEvent 'domready', ->
    root.accountDialog = new MooDialog {destroyOnHide: false}
    root.accountDialog.setContent $ 'account_box'

    new TinyTab $$('#toptabs li a'), $$('#tabs-body > span')

    $$('ul.nav').each (nav) ->
        new MooDropMenu nav, {
            onOpen: (el) -> el.fade 'in'
            onClose: (el) -> el.fade 'out'
            onInitialize: (el) -> el.fade('hide').set 'tween', {duration:500}
        }

    new SettingsUI()


class SettingsUI
    constructor: ->
        @menu = $$ "#general-menu li"
        @menu.append $$ "#plugin-menu li"

        @name = $ "tabsback"
        @general = $ "general_form_content"
        @plugin = $ "plugin_form_content"

        el.addEvent 'click', @menuClick.bind(this) for el in @menu

        $("general|submit").addEvent "click", @configSubmit.bind(this)
        $("plugin|submit").addEvent "click", @configSubmit.bind(this)

        $("account_add").addEvent "click", (e) ->
            root.accountDialog.open()
            e.stop()

        $("account_reset").addEvent "click", (e) ->
            root.accountDialog.close()

        $("account_add_button").addEvent "click", @addAccount.bind(this)
        $("account_submit").addEvent "click", @submitAccounts.bind(this)


    menuClick: (e) ->
        [category, section] = e.target.get("id").split("|")
        name = e.target.get "text"


        target = if category is "general" then @general else @plugin
        target.dissolve()

        new Request({
            "method" : "get"
            "url" : "/json/load_config/#{category}/#{section}"
            "onSuccess": (data) =>
                target.set "html", data
                target.reveal()
                this.name.set "text", name
        }).send()


    configSubmit: (e) ->
        category = e.target.get("id").split("|")[0];
        form = $("#{category}_form");

        form.set "send", {
            "method": "post"
            "url": "/json/save_config/#{category}"
            "onSuccess" : ->
                root.notify.alert '{{ _("Settings saved.")}}', {
                            'className': 'success'
                        }
            "onFailure": ->
                root.notify.alert '{{ _("Error occured.")}}', {
                            'className': 'error'
                        }
        }
        form.send()
        e.stop()

    addAccount: (e) ->
        form = $ "add_account_form"
        form.set "send", {
            "method": "post"
            "onSuccess" : -> window.location.reload()
            "onFailure": ->
                root.notify.alert '{{_("Error occured.")}}', {
                    'className': 'error'
                    }
            }

        form.send()
        e.stop()
    
    submitAccounts: (e) ->
        form = $ "account_form"
        form.set "send", {
             "method": "post",
             "onSuccess" : -> window.location.reload()
             "onFailure": ->
                 root.notify.alert('{{ _("Error occured.") }}', {
                             'className': 'error'
                         });
             }

        form.send()
        e.stop()