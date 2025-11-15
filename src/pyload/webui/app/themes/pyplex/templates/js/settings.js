{% autoescape true %}

$(() => new SettingsUI());

if (!String.prototype.startsWith) {
  String.prototype.startsWith = function(searchString, position = 0) {
    return this.indexOf(searchString, position) === position;
  };
}

class SettingsUI {
  constructor() {
    this.generalPanel = $("#core_form_content");
    this.pluginPanel = $("#plugin_form_content");

    const activeTab = sessionStorage.getItem('activeTab');
    if (activeTab) {
      sessionStorage.removeItem('activeTab');
      $(`#toptabs a[href="${activeTab}"]`).tab('show');
    }

    this.initEventListeners();
    this.initUsersAdmin();
    this.initPluginSearch();
    this.initPathChooser();
  };

  initEventListeners() {
    $("#quit-pyload").click(() => {
      uiHandler.yesNoDialog("{{_('You are really sure you want to quit pyLoad?')}}", (answer) => {
        if (answer) {
          this.quitPyload();
        }
      });
    });

    $("#restart-pyload").click(() => {
      uiHandler.yesNoDialog("{{_('Are you sure you want to restart pyLoad?')}}", (answer) => {
        if (answer) {
          this.restartPyload();
        }
      });
    });

    $('a[data-toggle="tab"]').on('shown.bs.tab', (event) => {
      if (event.target !== event.relatedTarget && $(event.target).attr("href") === "#accounts") {
        $('#account_form input[type=checkbox]').prop("checked", false);
      }
    });

    $("#core-menu").find("li").each((_, element) => {
      $(element).click(this.menuClick.bind(this));
    });

    $("#core_submit").click(this.configSubmit.bind(this));
    $("#plugin_submit").click(this.configSubmit.bind(this));
    $("#account_add_button").click(this.addAccount.bind(this));
    $("#account_submit").click(this.submitAccounts.bind(this));
    $("#account_add").click(() => $("#add_account_form").trigger("reset"));
    $("#user_submit").click(this.submitUsers.bind(this));
  }

  restartPyload() {
    $.post("{{url_for('api.rpc', func='restart')}}")
      .done(() => {
        $('#restart_box').modal('hide');
        $('#content').addClass("hidden");
        $('#restart_msg').removeClass("hidden");
        setTimeout(() => {
          window.location = "{{url_for('app.dashboard')}}";
        }, 10000);
      })
      .fail(() => {
        uiHandler.indicateFail("{{_('Error occurred')}}");
      });
  };

  quitPyload() {
    $.post("{{url_for('api.rpc', func='kill')}}")
      .done(() => {
        $('#quit_box').modal('hide');
        $('#content').addClass("hidden");
        $('#shutdown_msg').removeClass("hidden");
      })
      .fail(() => {
        uiHandler.indicateFail("{{_('Error occurred')}}");
      });
  };

  initUsersAdmin() {
    $("#password_box").on('click', '#login_password_button', (event) => {
      const passwd = $("#login_new_password").val();
      const passwdConfirm = $("#login_new_password2").val();
      if (passwd === passwdConfirm) {
        $.ajax({
          method: "POST",
          url: "{{url_for('json.change_password')}}",
          data: $("#password_form").serialize(),
          async: true,
          success: () => {
            uiHandler.indicateSuccess("{{_('Password successfully changed')}}");
          }
        }).fail(() => {
          uiHandler.indicateFail("{{_('Error occurred')}}");
        });
        $('#password_box').modal('hide');
      } else {
        alert("{{_('Passwords did not match.')}}");
      }
      event.stopPropagation();
      event.preventDefault();
    });

    $(".is_admin").each(function() {
      const userName = $(this).attr("name").split("|")[0];
      $(this).on("change", { userName }, function(event) {
        const checked = $(this).is(":checked");
        const permsList = $(`#${userName}\\|perms`);
        permsList.prop('disabled', checked);
        if (checked) {
          permsList.val([]);
        }
      });
    });

    $(".change_password").each(function() {
      const userName = $(this).attr("id").split("|")[1];
      $(this).on("click", { userName }, function(event) {
        $("#password_form").trigger("reset");
        $("#password_box #user_login").val(userName);
      });
    });

    $('#password_box').on('shown.bs.modal', () => {
      $('#login_current_password').focus();
    });

    $("#user_add").click(() => {
      $("#new_perms").prop('disabled', false);
      $("#user_add_form").trigger("reset");
    });

    $("#new_role").change(function() {
      const checked = $(this).is(":checked");
      const permsList = $("#new_perms");
      permsList.prop('disabled', checked);
      if (checked) {
        permsList.val([]);
      }
    });

    $("#new_user_button").click(function(event) {
      $(this).prop('disabled', true);
      const $userForm = $("#user_add_form");
      const $userName = $("#new_user");
      if ($userName.val().trim() === "") {
        alert("{{_('Username must be filled out')}}");
      } else {
        $userName.val($userName.val().trim());
        const passwd = $("#new_password").val();
        const passwdConfirm = $("#new_password2").val();
        if (passwd === passwdConfirm) {
          $.ajax({
            method: "POST",
            url: "{{url_for('json.add_user')}}",
            async: true,
            data: $userForm.serialize(),
            success: () => {
              sessionStorage.setItem("activeTab", "#users");
              window.location.assign(window.location.href);
            }
          }).fail(() => {
            uiHandler.indicateFail("{{_('Error occurred')}}");
          });
          $('#user_box').modal('hide');
        } else {
          alert("{{_('Passwords did not match.')}}");
        }
      }
      $(this).prop('disabled', false);
      event.stopPropagation();
      event.preventDefault();
    });
  }

  initPluginSearch() {
    const resultTemplate = $('#result-template').contents();
    const noresultTemplate = $('#noresult-template').contents();
    const pluginListPanel = $('#plugin-menu');
    const searchInput = $('#query-text');
    const pluginList = $('#plugins-list').data('plugin');

    const search = (query) => {
      let results = [];
      if (query) {
        results = pluginList.filter(p => p[1].toLowerCase().includes(query.toLowerCase()));
      } else {
        results = pluginList;
      }

      pluginListPanel.empty();

      if (results.length) {
        results.forEach(p => {
          resultTemplate.clone().find('.plugin-row')
            .attr('id', `plugin|${p[0]}`)
            .text(p[1])
            .removeAttr('class')
            .click(this.menuClick.bind(this))
            .end().appendTo(pluginListPanel);
        });
      } else {
        pluginListPanel.append(noresultTemplate);
      }
    };

    searchInput.attr('placeholder', "{{_('Name of plugin')}}");
    searchInput.prop('disabled', false);
    searchInput.on('input', () => {
      const query = searchInput.val();
      const visible = Boolean(query);
      searchInput.siblings('.close').toggleClass('hidden', !visible);
      search(query.trim());
    });
    searchInput.siblings('.close').click(() => {
      searchInput.val('').focus().trigger('input');
    });
    searchInput.focus();
    searchInput.trigger('input');
  }

  menuClick(event) {
    const [category, section] = $(event.currentTarget).attr('id').split('|');
    const panel = category === 'core' ? this.generalPanel : this.pluginPanel;
    $.get({
      url: "{{url_for('json.load_config')}}",
      data: { category, section },
      traditional: true,
      success: (response) => {
        panel.html(response);
      }
    });
  }

  configSubmit(event) {
    const category = $(event.currentTarget).attr('id').split("_")[0];
    $.ajax({
      method: "POST",
      url: `{{url_for('json.save_config')}}?category=${category}`,
      data: $(`#${category}_form`).serialize(),
      async: true,
      success: () => {
        uiHandler.indicateSuccess("{{_('Settings saved')}}");
      }
    }).fail(() => {
      uiHandler.indicateFail("{{_('Error occurred')}}");
    });
    event.stopPropagation();
    event.preventDefault();
  }

  addAccount(event) {
    $(event.currentTarget).prop('disabled', true);
    $.ajax({
      method: "POST",
      url: "{{url_for('json.add_account')}}",
      async: true,
      data: $("#add_account_form").serialize(),
      success: () => {
        sessionStorage.setItem("activeTab", "#accounts");
        window.location.reload();
      }
    }).fail(() => {
      uiHandler.indicateFail("{{_('Error occurred')}}");
    });
    event.preventDefault();
  }

  submitUsers(event) {
    uiHandler.indicateLoad();
    $.ajax({
      method: "POST",
      url: "{{url_for('json.update_users')}}",
      data: $("#user_form").serialize(),
      async: true,
      success: () => {
        sessionStorage.setItem("activeTab", "#users");
        window.location.reload();
      }
    }).fail(() => {
      uiHandler.indicateFail("{{_('Error occurred')}}");
    });
    event.preventDefault();
  }

  submitAccounts(event) {
    uiHandler.indicateLoad();
    $.ajax({
      method: "POST",
      url: "{{url_for('json.update_accounts')}}",
      data: $("#account_form").serialize(),
      async: true,
      success: () => {
        sessionStorage.setItem("activeTab", "#accounts");
        window.location.reload();
      }
    }).fail(() => {
      uiHandler.indicateFail("{{_('Error occurred')}}");
    });
    event.preventDefault();
  }

  initPathChooser() {
    $("#path_type0, #path_type1").click(function() {
      const iframe = document.getElementById('chooser_ifrm').contentWindow;
      const isAbsolute = $(this).val() === "1";
      if (isAbsolute !== iframe.isabsolute) {
        iframe.location.href = isAbsolute ? iframe.abspath : iframe.relpath;
      }
      return false;
    });

    $("#path_chooser").on("show.bs.modal", (e) => {
      const chooserIfrm = $(e.currentTarget).find("#chooser_ifrm");
      const browseFor = $(e.relatedTarget).data('browsefor');
      const targetInput = $(e.relatedTarget).data('targetinput').replace("|", "\\|");

      if (browseFor) {
        chooserIfrm.height(Math.max($(window).height() - 200, 150));
        const val = targetInput ? encodeURIComponent($(targetInput).val()) : "";
        $(e.currentTarget).data('targetinput', targetInput);
        if (browseFor === "file") {
          $(e.currentTarget).find("#chooser_title").text("{{_('Select File')}}");
          chooserIfrm.attr("src", `{{url_for('app.filechooser')}}?path=${val}`);
        } else if (browseFor === "folder") {
          $(e.currentTarget).find("#chooser_title").text("{{_('Select Folder')}}");
          chooserIfrm.attr("src", `{{url_for('app.pathchooser')}}?path=${val}`);
        }
      }
    });

    $("#chooser_confirm_button").click((event) => {
      const dialog = $("#path_chooser");
      const targetInput = dialog.data('targetinput');
      if (targetInput) {
        $(targetInput).val(dialog.find("#path_p").text());
      }
      dialog.modal('hide');
      event.preventDefault();
    });
  }

  pathchooserChanged(iframe) {
    const path_p = $("#path_p");
    path_p.text(iframe.cwd);
    path_p.prop("title", iframe.cwd);
    $("#chooser_confirm_button").prop("disabled", !iframe.submit);
    $("#path_type0").prop("checked", !iframe.isabsolute);
    $("#path_type1").prop("checked", iframe.isabsolute);
  }
}

{% endautoescape %}
