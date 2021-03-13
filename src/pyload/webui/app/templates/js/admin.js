{% autoescape true %}

document.addEvent("domready", function() {

    window.passwordDialog = new MooDialog({destroyOnHide: false});
    window.passwordDialog.setContent($('password_box'));
    window.userDialog = new MooDialog({destroyOnHide: false});
    window.userDialog.setContent($('user_box'));

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
});

{% endautoescape %}
