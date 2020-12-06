{% autoescape true %}

$(function() {
    $("#password_box").on('click', '#login_password_button', function (event) {
        let passwd = $("#login_new_password").val();
        let passwdConfirm = $("#login_new_password2").val();
        if (passwd === passwdConfirm) {
            $.ajax({
                method: "post",
                url: "{{url_for('json.change_password')}}",
                data: $("#password_form").serialize(),
                async: true,
                success: function () {
                    indicateSuccess("{{_('Settings saved')}}");
                }
            })
            .fail(function () {
                indicateFail("{{_('Error occurred')}}");
            });
            $('#password_box').modal('hide');
        } else {
            alert("{{_('Passwords did not match.')}}")
        }
        event.stopPropagation();
        event.preventDefault();
    });
    $(".is_admin").each(function () {
        let userName = $(this).attr("name").split("|")[0];
        $(this).bind("change", {userName: userName}, function (event) {
            let checked = $(this).is(":checked");
            let permsList = $("#" + userName + "\\|perms");
            permsList.attr('disabled', checked);
            if (checked) {
                permsList.val([]);
            }
        });
    });
    $(".change_password").each(function () {
        let userName = $(this).attr("id").split("|")[1];
        $(this).bind("click", {userName: userName}, function (event) {
            $("#password_form").trigger("reset");
            $("#password_box #user_login").val(userName);
        });
    });
    $('#password_box').on('shown.bs.modal', function () {
        $('#login_current_password').focus();
    })
    $("#user_add").click(function (event) {
        $("#user_add_form").trigger("reset");
    });
    $("#new_role").change(function (event) {
        let checked = $(this).is(":checked");
        let permsList = $("#new_perms");
        permsList.attr('disabled', checked);
        if (checked) {
            permsList.val([]);
        }
    });
    $("#new_user_button").click(function (event) {
        $(this).attr('disabled', true);
        let $userForm = $("#user_add_form");
        let $userName = $("#new_user");
        if ($userName.val().trim() === "") {
            alert("{{_('Username must be filled out')}}");
        } else {
            $userName.val($userName.val().trim());
            let passwd = $("#new_password").val();
            let passwdConfirm = $("#new_password2").val();
            if (passwd === passwdConfirm) {
                $.ajax({
                    method: "post",
                    url: "{{url_for('json.add_user')}}",
                    async: true,
                    data: $userForm.serialize(),
                    success: function () {
                        window.location.assign(window.location.href);
                    }
                })
                .fail(function () {
                    indicateFail("{{_('Error occurred')}}");
                });
                $('#user_box').modal('hide');
            } else {
                alert("{{_('Passwords did not match.')}}")
            }
        }
        $(this).attr('disabled', false);
        event.stopPropagation();
        event.preventDefault();
    });
});

{% endautoescape %}
