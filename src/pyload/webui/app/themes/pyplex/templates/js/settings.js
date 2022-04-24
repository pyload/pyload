{% autoescape true %}

$(function() {
    return new SettingsUI();
});

if (!String.prototype.startsWith) {
  String.prototype.startsWith = function(searchString, position) {
    position = position || 0;
    return this.indexOf(searchString, position) === position;
  };
}

SettingsUI = (function() {
    function a() {
        $("#quit_box").on('click', '#quit_button', function () {
            $.get("{{url_for('api.rpc', func='kill')}}", function() {
                $('#quit_box').modal('hide');
                $('#content').addClass("hidden");
                $('#shutdown_msg').removeClass("hidden");
            })
            .fail(function () {
                indicateFail("{{_('Error occurred')}}");
            });
        });

        $("#restart_box").on('click', '#restart_button', function () {
            $.get("{{url_for('api.rpc', func='restart')}}", function() {
                $('#restart_box').modal('hide');
                $('#content').addClass("hidden");
                $('#restart_msg').removeClass("hidden");
                setTimeout(function() {
                    window.location = "{{url_for('app.dashboard')}}";
                }, 10000);
            })
            .fail(function () {
                indicateFail("{{_('Error occurred')}}");
            });
        });
        let activeTab = sessionStorage.getItem('activeTab');
        if (activeTab) {
            sessionStorage.removeItem('activeTab');
            $('#toptabs a[href="' + activeTab + '"]').tab('show');
        }
        $('a[data-toggle="tab"]').on('shown.bs.tab', function(event) {
            if (event.target !== event.relatedTarget && $(event.target).attr("href") === "#accounts") {
                $('#account_form input[type=checkbox]').each(function() {
                    $(this).prop("checked", false);
                })
            }
        });

        generalPanel = $("#core_form_content");
        pluginPanel = $("#plugin_form_content");
        thisObject = this;
        $("#core-menu").find("li").each(function(a) {
            $(this).click(thisObject.menuClick);
        });

        $("#core_submit").click(this.configSubmit);
        $("#plugin_submit").click(this.configSubmit);
        $("#account_add_button").click(this.addAccount);
        $("#account_submit").click(this.submitAccounts);
        $("#account_add").click(function() {
            $("#add_account_form").trigger("reset");
        });
        $("#user_submit").click(this.submitUsers);

        this.initUsersAdmin();
        this.initPluginSearch();
        this.initPathcooser();
    }
    a.prototype.initUsersAdmin = function() {
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
                        indicateSuccess("{{_('Password successfully changed')}}");
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
            $("#new_perms").attr('disabled', false);
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
                            sessionStorage.setItem("activeTab", "#users");
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
    };
    a.prototype.initPluginSearch = function() {
        var b, i;
        resultTemplate = $('#result-template').contents();
        noresultTemplate = $('#noresult-template').contents();
        pluginListPanel = $('#plugin-menu');
        searchInput = $('#query-text');

        var pluginList = $('#plugins-list').data('plugin');

        function search(query) {
            var results = [];
            if (query) {
                pluginList.forEach(function(p) {
                    if (p[1].toLowerCase().startsWith(query.toLowerCase())) {
                        results.push(p);
                    }
                })
            } else {
                results = pluginList;
            }

            pluginListPanel.empty();

            if (results.length) {
                results.forEach(function (p) {
                    resultTemplate.clone().find('.plugin-row')
                        .attr('id', 'plugin|'.concat(p[0]))
                        .text(p[1])
                        .removeAttr('class')
                        .click(thisObject.menuClick)
                        .end().appendTo(pluginListPanel);
                });
            } else {
                pluginListPanel.append(noresultTemplate);
            }
        }

        searchInput.attr('placeholder', "{{_('Name of plugin')}}");
        searchInput.removeAttr('disabled');
        searchInput.on('input', function () {
            var query = searchInput.val();
            var visible = Boolean(query);
            searchInput.siblings('.close').toggleClass('hidden', !visible);
            search(query.trim());
        });
        searchInput.siblings('.close').click(function() {
            searchInput.val('').focus().trigger('input');
        });
        searchInput.focus();
        searchInput.trigger('input')

    };
    a.prototype.menuClick = function(h) {
        var c, b, g, f, d;
        d = $(this).attr('id').split('|'), c = d[0], g = d[1];
        b = $(this).text();
        f = c === 'core' ? generalPanel : pluginPanel;
        $.get({
            url: "{{url_for('json.load_config')}}",
            data: {category: c, section: g},
            traditional: true,
            success: function(e) {
                f.html(e);
            }
        })
    };
    a.prototype.configSubmit = function(d) {
        var category, b;
        category = $(this).attr('id').split("_")[0];
        $.ajax({
            method: "post",
            url: "{{url_for('json.save_config')}}" + "?category=" + category,
            data: $("#" + category + "_form").serialize(),
            async: true,
            success: function () {
                indicateSuccess("{{_('Settings saved')}}");
            }
        })
        .fail(function () {
            indicateFail("{{_('Error occurred')}}");
        });
        d.stopPropagation();
        d.preventDefault();
    };
    a.prototype.addAccount = function(c) {
        $(this).attr('disabled', true);
        $.ajax({
            method: "post",
            url: "{{url_for('json.add_account')}}",
            async: true,
            data: $("#add_account_form").serialize(),
            success: function () {
                sessionStorage.setItem("activeTab", "#accounts");
                return window.location.reload();
            }
        })
        .fail(function() {
            indicateFail("{{_('Error occurred')}}");
        });
        $(this).attr('disabled', false);
        c.preventDefault();
    };
    a.prototype.submitAccounts = function(c) {
        indicateLoad();
        $.ajax({
            method: "post",
            url: "{{url_for('json.update_accounts')}}",
            data: $("#account_form").serialize(),
            async: true,
            success: function () {
                sessionStorage.setItem("activeTab", "#accounts");
                return window.location.reload();
            }
        })
        .fail(function() {
            indicateFail("{{_('Error occurred')}}");
        });
        c.preventDefault();
    };
    a.prototype.submitUsers = function(c) {
        indicateLoad();
        $.ajax({
            method: "post",
            url: "{{url_for('json.update_users')}}",
            data: $("#user_form").serialize(),
            async: true,
            success: function () {
                sessionStorage.setItem("activeTab", "#users");
                return window.location.reload();
            }
        })
        .fail(function() {
            indicateFail("{{_('Error occurred')}}");
        });
        c.preventDefault();
    };
    a.prototype.initPathcooser = function () {
        $("#path_type0, #path_type1").click(function () {
            var iframe = document.getElementById('chooser_ifrm').contentWindow;
            var isabsolute = $(this).val() === "1";
            if (isabsolute !== iframe.isabsolute) {
                iframe.location.href = isabsolute ? iframe.abspath : iframe.relpath;
            }
            return false;
        });
        $("#path_chooser").on("show.bs.modal", function (e) {
            var chooserIfrm = $(this).find("#chooser_ifrm");
            var browseFor = $(e.relatedTarget).data('browsefor');
            var targetInput = $(e.relatedTarget).data('targetinput').replace("|", "\\|");

            if (browseFor) {
                chooserIfrm.height(Math.max($(window).height()-200,  150));
                var val = targetInput ? encodeURIComponent($(targetInput).val()) : "";
                $(this).data('targetinput', targetInput);
                if (browseFor === "file") {
                    $(this).find("#chooser_title").text("{{_('Select File')}}");
                    chooserIfrm.attr("src", "{{url_for('app.filechooser')}}?path=" + val);
                }
                else if (browseFor === "folder") {
                    $(this).find("#chooser_title").text("{{_('Select Folder')}}");
                    chooserIfrm.attr("src", "{{url_for('app.pathchooser')}}?path=" + val);
                }
            }
        });
        $("#chooser_confirm_button").click(function () {
            var dialog = $("#path_chooser");
            var targetInput = dialog.data('targetinput');
            if (targetInput) {
                $(targetInput).val(dialog.find("#path_p").text());
            }
            dialog.modal('hide');
            event.preventDefault();
        });
    };
    a.prototype.pathchooserChanged = function(iframe) {
        var path_p = $("#path_p");
        path_p.text(iframe.cwd);
        path_p.prop("title", iframe.cwd);
        $("#chooser_confirm_button").attr("disabled", !iframe.submit);
        $("#path_type0").prop("checked", !iframe.isabsolute);
        $("#path_type1").prop("checked", iframe.isabsolute);
    };
    return a;
})();

{% endautoescape %}
