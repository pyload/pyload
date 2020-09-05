{% autoescape true %}

$(function() {
    $("#password_box").on('click', '#login_password_button', function (event) {
        let passwd = $("#login_new_password").val();
        let passwdConfirm = $("#login_new_password2").val();
        if (passwd === passwdConfirm) {
            $.ajax({
                method: "post",
                url: "/json/change_password",
                data: $("#password_form").serialize(),
                async: true,
                success: function () {
                    indicateSuccess("{{_('Settings saved')}}");
                }
            })
            .fail(function() {
                indicateFail("{{_('Error occurred')}}");
            });
            $('#password_box').modal('hide');
        } else {
            alert("{{_('Passwords did not match.')}}")
        }
        event.stopPropagation();
        event.preventDefault();
    });
    $(".change_password").each(function () {
        let userName = $(this).attr("id").split("|")[1];
        $(this).bind("click",{userName:userName}, function(g) {
            $("#password_box #user_login").val(userName);
        });
    });

    $("#quit_box").on('click', '#quit_button', function () {
        $.get("/api/kill", function() {
            $('#quit_box').modal('hide');
            $('#content').addClass("hidden");
            $('#shutdown_msg').removeClass("hidden");
        });
    });

    $("#restart_box").on('click', '#restart_button', function () {
        $.get("/api/restart", function() {
            $('#restart_box').modal('hide');
            $('#content').addClass("hidden");
            $('#restart_msg').removeClass("hidden");
            setTimeout(function() {
                window.location = "/dashboard";
            }, 10000);
        });
    });
});

{% endautoescape %}
