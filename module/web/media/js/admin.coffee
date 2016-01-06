root = this

window.addEvent "domready", ->

    root.passwordDialog = new MooDialog {destroyOnHide: false}
    root.passwordDialog.setContent $ 'password_box'

    $("login_password_reset").addEvent "click", (e) -> root.passwordDialog.close()
    $("login_password_button").addEvent "click", (e) ->

        newpw = $("login_new_password").get("value")
        newpw2 = $("login_new_password2").get("value")

        if newpw is newpw2
            form = $("password_form")
            form.set "send", {
                onSuccess: (data) ->
                    root.notify.alert "Success", {
                            'className': 'success'
                        }
                onFailure: (data) ->
                    root.notify.alert "Error", {
                            'className': 'error'
                        }
                }

            form.send()

            root.passwordDialog.close()
        else
            alert '{{_("Passwords did not match.")}}'

        e.stop()

    for item in $$(".change_password")
        id = item.get("id")
        user = id.split("|")[1]
        $("user_login").set("value", user)
        item.addEvent "click", (e) -> root.passwordDialog.open()

    $('quit-pyload').addEvent "click", (e) ->
        new MooDialog.Confirm "{{_('You are really sure you want to quit pyLoad?')}}", ->
            new Request.JSON({
                url: '/api/kill'
                method: 'get'
            }).send()
        , ->
        e.stop()

    $('restart-pyload').addEvent "click", (e) ->
        new MooDialog.Confirm "{{_('Are you sure you want to restart pyLoad?')}}", ->
            new Request.JSON({
                url: '/api/restart'
                method: 'get'
                onSuccess: (data) -> alert "{{_('pyLoad restarted')}}"
            }).send()
        , ->
        e.stop()