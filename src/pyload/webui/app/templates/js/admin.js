/*
 * decaffeinate suggestions:
 * DS101: Remove unnecessary use of Array.from
 * DS102: Remove unnecessary code created because of implicit returns
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */

{% autoescape true %}

document.addEvent("domready", function() {

    window.passwordDialog = new MooDialog({destroyOnHide: false});
    window.passwordDialog.setContent($('password_box'));

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

    for (let item of Array.from($$(".change_password"))) {
        const id = item.get("id");
        const user = id.split("|")[1];
        $("user_login").set("value", user);
        item.addEvent("click", e => window.passwordDialog.open());
    }

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
