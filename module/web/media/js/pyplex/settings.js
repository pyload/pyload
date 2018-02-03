{% autoescape true %}
var SettingsUI, root;
root = this;

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
        var c, e, b, d;

        var activeTab = sessionStorage.getItem('activeTab');
        if (activeTab) {
            sessionStorage.removeItem('activeTab');
            $('#toptabs a[href="' + activeTab + '"]').tab('show');
        }

        generalPanel = $("#general_form_content");
        pluginPanel = $("#plugin_form_content");
        thisObject = this;
        $("#general-menu").find("li").each(function(a) {
            $(this).click(thisObject.menuClick);
        });

        $("#general_submit").click(this.configSubmit);
        $("#plugin_submit").click(this.configSubmit);
        $("#account_add").click(function(f) {
            $("#account_box").modal('show');
            f.stopPropagation();
            f.preventDefault();
        });
        $("#account_add_button").click(this.addAccount);
        $("#account_submit").click(this.submitAccounts);

        this.initPluginSearch();
        this.initPathcooser();
    }
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
        f = c === 'general' ? generalPanel : pluginPanel;
        $.get( "{{'/json/load_config/'|url}}" + c + '/' + g, function(e) {
                f.html(e);
            });
    };
    a.prototype.configSubmit = function(d) {
        var c, b;
        c = $(this).attr('id').split("_")[0];
        $.ajax({
            method: "post",
            url: "{{'/json/save_config/'|url}}" + c,
            data: $("#" + c + "_form").serialize(),
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
        $(this).addClass("disabled");
        $.ajax({
            method: "post",
            url: "{{'/json/add_account'|url}}",
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
        c.preventDefault();
    };
    a.prototype.submitAccounts = function(c) {
        indicateLoad();
        $.ajax({
            method: "post",
            url: "{{'/json/update_accounts'|url}}",
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
                var val = targetInput ? $(targetInput).val().replace("../", "::%2F").replace("..\\", "::%2F") : "";
                $(this).data('targetinput', targetInput);
                if (browseFor === "file") {
                    $(this).find("#chooser_title").text("{{_('Select File')}}");
                    chooserIfrm.attr("src", "{{'/filechooser/'|url}}" + val);
                }
                else if (browseFor === "folder") {
                    $(this).find("#chooser_title").text("{{_('Select Folder')}}");
                    chooserIfrm.attr("src", "{{'/pathchooser/'|url}}" + val);
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
        $("#chooser_confirm_button").toggleClass("disabled", !iframe.submit );
        $("#path_type0").prop("checked", iframe.isabsolute ? "" : "checked");
        $("#path_type1").prop("checked", iframe.isabsolute ? "checked" : "");
    };
    return a;
})(); 
{% endautoescape %}