{% autoescape true %}
var root;
root = this;
$(function() {
    var f, c, b, e, a, d;
    $("#password_box").on('click', '#login_password_button', function (j) {
        var h, i, g;
        i = $("#login_new_password").val();
        g = $("#login_new_password2").val();
        if (i === g) {
            $.ajax({
                method: "post",
                url: "{{'/json/change_password'|url}}",
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
        j.stopPropagation();
        j.preventDefault();
    });
    $(".change_password").each(function () {
        userName = $(this).attr("id").split("|")[1];
        $(this).bind("click",{userName:userName}, function(g) {
            $("#password_box #user_login").val(userName);
        });
    });

    $("#quit_box").on('click', '#quit_button', function () {
        $.get( "{{'/api/kill'|url}}", function() {
            $('#quit_box').modal('hide');
            $('#content').addClass("hidden");
            $('#shutdown_msg').removeClass("hidden");
        });
    });

    $("#restart_box").on('click', '#restart_button', function () {
        $.get( "{{'/api/restart'|url}}", function() {
            $('#restart_box').modal('hide');
            $('#content').addClass("hidden");
            $('#restart_msg').removeClass("hidden");
            setTimeout(function() {
                window.location = "{{'/home'|url}}";
            }, 10000);
        });
    });
}); 
{% endautoescape %}