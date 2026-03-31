{% autoescape true %}

$(() => new SettingsUI());

if (!String.prototype.startsWith) {
  String.prototype.startsWith = function(searchString, position = 0) {
    return this.indexOf(searchString, position) === position;
  };
}

function timestampToLocalISOTime(timestamp) {
  const offset = timestamp.getTimezoneOffset() * 60000;
  const localISOTime = new Date(timestamp - offset).toISOString().slice(0, 16);
  return localISOTime;
}

class SettingsUI {
  constructor() {
    this.generalPanel = $("#core_form_content");
    this.pluginPanel = $("#plugin_form_content");

    this.initEventListeners();
    this.initUsersAdmin();
    this.initPluginSearch();
    this.initPathChooser();
    this.apikeysUI = new ApikeysUI();

    const activeTab = sessionStorage.getItem('activeTab');
    if (activeTab) {
      sessionStorage.removeItem('activeTab');
      $(`#toptabs a[href="${activeTab}"]`).tab('show');
    }
  };

  initEventListeners() {
    $("#quit-pyload").click(() => {
      uiHandler.yesNoDialog("{{_('Are you really sure you want to quit pyLoad?')}}", (answer) => {
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
      if (event.currentTarget !== event.relatedTarget && $(event.currentTarget).attr("href") === "#accounts") {
        $('#account_form input[type=checkbox]').prop("checked", false);
      }
    });

    $("#core-menu").on('click', 'li', this.menuClick.bind(this));
    $("#core_submit").click(this.configSubmit.bind(this));
    $("#plugin_submit").click(this.configSubmit.bind(this));
    $("#account_add_button").click(this.addAccount.bind(this));
    $("#account_submit").click(this.submitAccounts.bind(this));
    $("#account_add").click(() => $("#add_account_form").trigger("reset"));
    {% if user.is_admin %}
      $("#user_submit").click(this.submitUsers.bind(this));
    {% endif %}
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
      const passwd = $("#user_newpw").val();
      const $passwdConfirm = $("#user_confpw");
      const passwdConfirm = $passwdConfirm.prop('disabled', true).val();
      if (passwd === passwdConfirm) {
        $.post({
          url: "{{url_for('json.change_password')}}",
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify(formToObject("#password_form")),
          success: () => {
            uiHandler.indicateSuccess("{{_('Password successfully changed')}}");
          }
        }).fail(() => {
          uiHandler.indicateFail("{{_('Error occurred')}}");
        }).always(() => {
          $passwdConfirm.prop('disabled', false);
        });
        $('#password_box').modal('hide');
      } else {
        alert("{{_('Passwords did not match.')}}");
      }
      event.stopPropagation();
      event.preventDefault();
    });

    $(document).on("change", ".is_admin", (event) => {
      const userName = $(event.currentTarget).attr("name").split("|")[0];
      const checked = $(event.currentTarget).is(":checked");
      const permsList = $(`#${userName}\\|perms`);

      permsList.prop("disabled", checked);
      if (checked) {
        permsList.val([]);
      }
    });

    $(document).on("click", ".change_password", (event) => {
      const userName = $(event.target).attr("id").split("|")[0];

      $("#password_form").trigger("reset");
      $("#password_box #user_login").val(userName);
    });

    $('#password_box').on('shown.bs.modal', () => {
      $('#user_curpw').focus();
    });

    $("#user_add").click(() => {
      $("#new_perms").prop('disabled', false);
      $("#user_add_form").trigger("reset");
    });

    $(document).off("click", ".delete_user").on("click", ".delete_user", (event) => {
      const userName = $(event.currentTarget).attr("id").split("|")[0];
      uiHandler.yesNoDialog("{{_('Are you sure you want to delete the user {}?')}}".replace("{}", userName), (answer) => {
          if (answer) {
            uiHandler.indicateLoad();
            $.post({
              url: "{{url_for('json.update_users')}}",
              dataType: 'json',
              contentType: 'application/json',
              data: JSON.stringify({update_data: {[`${userName}|delete`]: true}}),
              success: () => {
                sessionStorage.setItem("activeTab", "#users");
                window.location.assign(window.location.href.replace(/#.*$/, ''));
              }
            }).fail(() => {
              uiHandler.indicateFail("{{_('Error occurred')}}");
            });
          }
          event.stopPropagation();
          event.preventDefault();
        }
      );
    });

    $("#new_role").change((event) => {
      const checked = $(event.currentTarget).is(":checked");
      const permsList = $("#new_perms");
      permsList.prop('disabled', checked);
      if (checked) {
        permsList.val([]);
      }
    });

    $("#new_user_button").click((event) => {
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
          $.post({
            url: "{{url_for('json.add_user')}}",
            data: $userForm.serialize(),
            success: () => {
              sessionStorage.setItem("activeTab", "#users");
              window.location.assign(window.location.href.replace(/#.*$/, ''));
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

      pluginListPanel.empty().on('click', 'li', this.menuClick.bind(this));

      if (results.length) {
        const $fragment = $(document.createDocumentFragment());
        results.forEach(p => {
          resultTemplate.clone().find('.plugin-row')
            .attr('id', `plugin|${p[0]}`)
            .text(p[1])
            .removeAttr('class')
            .end()
            .appendTo($fragment);
        });
        pluginListPanel.append($fragment);
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
    $.post({
      url: "{{url_for('json.save_config')}}",
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify({category: category, config: formToObject(`#${category}_form`)}),
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
    $.post({
      url: "{{url_for('json.add_account')}}",
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify(formToObject("#add_account_form")),
      success: () => {
        sessionStorage.setItem("activeTab", "#accounts");
        window.location.assign(window.location.href.replace(/#.*$/, ''));
      }
    }).fail(() => {
      uiHandler.indicateFail("{{_('Error occurred')}}");
    });
    event.preventDefault();
  }

  submitUsers(event) {
    uiHandler.indicateLoad();
    $.post({
      url: "{{url_for('json.update_users')}}",
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify({update_data: formToObject("#user_form")}),
      success: () => {
        sessionStorage.setItem("activeTab", "#users");
        window.location.assign(window.location.href.replace(/#.*$/, ''));
      }
    }).fail(() => {
      uiHandler.indicateFail("{{_('Error occurred')}}");
    });
    event.preventDefault();
  }

  submitAccounts(event) {
    uiHandler.indicateLoad();
    $.post({
      url: "{{url_for('json.update_accounts')}}",
      data: $("#account_form").serialize(),
      success: () => {
        sessionStorage.setItem("activeTab", "#accounts");
        window.location.assign(window.location.href.replace(/#.*$/, ''));
      }
    }).fail(() => {
      uiHandler.indicateFail("{{_('Error occurred')}}");
    });
    event.preventDefault();
  }

  initPathChooser() {
    $("#path_type0, #path_type1").click(() => {
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

class ApikeysUI {
  constructor() {
    this.currentUserName = "";
    this.initApiKeyGen();
  }

  initApiKeyGen() {
    $('#apikeys_box').on('shown.bs.modal', (event) => {
      this.currentUserName = $(event.relatedTarget).attr("id").split("|")[0];
      this.loadApiKeys();
    }).off('click', '#apikeyAddBtn').on('click', '#apikeyAddBtn', (event) => {
      this.modalGenerateApikey().then((key) => {
        this.modalShowApikey(key).then(() => {
          this.loadApiKeys();
          this.modalSwitch("Main");
        })
      }).catch(() => {
        this.modalSwitch("Main");
      })
    }).off('click', '.delete_apikey').on('click', '.delete_apikey', (event) => {
      const keyId = $(event.currentTarget).attr("id").split("|")[0];
      uiHandler.yesNoDialog("{{_('Are you sure you want to delete this API key?')}}", (answer) => {
        if (answer) {
          this.deleteApiKey(keyId).then(() => {
            this.loadApiKeys();
          }).catch((errMsg) => {
            uiHandler.indicateFail(errMsg);
          })
        }
      });
    });
    this.modalSwitch("Main");
  }

  modalGenerateApikey() {
    return new Promise((resolve, reject) => {
      this.modalSwitch("Gen");
      $('#apikeyUser').val(this.currentUserName);
      const apikeyExpiration = $('#apikeyExpiration');
      const now = new Date();
      const plusOneMinute = new Date(now.getTime() + 60000);
      apikeyExpiration.attr('min', timestampToLocalISOTime(plusOneMinute));
      $("#apikeyGenSubmitBtn").off('click').on('click', (event) => {
        if ($("#apikeyGenForm")[0].reportValidity()) {
          $(event.currentTarget).prop('disabled', true);
          const password = $('#apikeyPassword').val().trim();
          const keyName = $('#apikeyName').val().trim();
          let expiresAt = apikeyExpiration.val().trim();
          expiresAt = expiresAt ? new Date(expiresAt).getTime() : 0
          if (this.currentUserName && password && keyName) {
            this.generateApiKey(password, keyName, expiresAt).then((key) => {
              resolve(key);
            }).catch((errMsg) => {
              uiHandler.indicateFail(errMsg);
              reject();
            });
          }
          $(event.currentTarget).prop('disabled', false);
        }
      });
      $("#apikeyGenCancelBtn").off('click').on('click', (event) => {
        reject();
      });
    })
  }

  modalShowApikey(key) {
    return new Promise((resolve) => {
      const apikeyKey = $("#apikeyGeneratedKey");
      this.modalSwitch("Copy");
      apikeyKey.val(key);
      $('#apikeyCopyDismissBtn').one('click', (event) => {
        apikeyKey.val("");
        resolve();
      })
      $('#apikeyCopyBtn').off('click').on('click', (event) => {
        const btn = $(event.currentTarget);
        navigator.clipboard.writeText(key).then(() => {
          const originalContent = btn.html();
          const originalClass = btn.attr('class');
          btn.html('<span class="glyphicon glyphicon-ok"></span> Copied!');
          btn.attr('class', "btn btn-success");
          setTimeout(() => {
            btn.html(originalContent);
            btn.attr('class', originalClass);
          }, 2500);
        })
      })
    })
  }

  modalSwitch(mode) {
    const modes = ["Main", "Gen", "Copy"]
    modes.forEach(m => {
      const methodName = m === mode ? "removeClass" : "addClass";
      $(`#apikey${m}Content`)[methodName]('hidden');
      $(`#apikey${m}Footer`)[methodName]('hidden');
    })
    $('#apikeyGenForm').trigger('reset');
    $('#apikeyCopyForm').trigger('reset');
    $("#apikeyGeneratedKey").val('');
  }

  loadApiKeys() {
    uiHandler.indicateLoad();
    const tbody = $('#apikeysTbody');
    $.post({
      url: "{{url_for('json.get_apikeys')}}",
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify({ user: this.currentUserName }),
      success: (response) => {
        uiHandler.indicateFinish();
        if (!response.success) {
          tbody.html('<tr><td colspan="5" class="text-danger">Error loading API keys</td></tr>');
          return;
        }

        if (!response.data || response.data.length === 0) {
          tbody.html('<tr><td colspan="5" class="text-center">No API keys yet</td></tr>');
          return;
        }

        let html = '';
        $.each(response.data, (index, keyInfo) => {
          const createdDate = new Date(keyInfo.created_at).toLocaleString();
          const expiresDate = keyInfo.expires_at ? new Date(keyInfo.expires_at).toLocaleString() : 'Never';
          const lastUsedDate = keyInfo.last_used ? new Date(keyInfo.last_used).toLocaleString() : 'Never';
          html += `
                    <tr>
                        <td>${keyInfo.name}</td>
                        <td>${createdDate}</td>
                        <td>${expiresDate}</td>
                        <td>${lastUsedDate}</td>
                        <td>
                            <button class="btn btn-xs btn-danger delete_apikey" id="${keyInfo.id}|delkey">
                                <span class="glyphicon glyphicon-trash"></span> Delete
                            </button>
                        </td>
                    </tr>
                `;
        });
        tbody.html(html);
      },
    }).fail(() => {
      uiHandler.indicateFinish();
      tbody.html('<tr><td colspan="5" class="text-danger">Error loading API keys</td></tr>');
    });
  }

  generateApiKey(password, keyName, expiresAt) {
    return new Promise((resolve, reject) => {
      uiHandler.indicateLoad();
      $.post({
        url: "{{url_for('json.generate_apikey')}}",
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
          user: this.currentUserName,
          password: password,
          name: keyName,
          expires: expiresAt,
        }),
        success: (response) => {
          uiHandler.indicateFinish();
          if (!response.success) {
            reject(response.error);
          } else {
            resolve(response.data.key);
          }
        }
      }).fail(() => {
        uiHandler.indicateFinish();
        reject("{{_('Error occurred')}}");
      });
    })
  }

  deleteApiKey(keyId) {
    return new Promise((resolve, reject) => {
      uiHandler.indicateLoad();
      $.post({
        url: "{{url_for('json.delete_apikey')}}",
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
          user: this.currentUserName,
          key: Number(keyId),
        }),
        success: (response)=> {
          uiHandler.indicateFinish();
          if (!response.success) {
            reject(response.error);
          } else {
            resolve();
          }
        }
      }).fail(() => {
        uiHandler.indicateFinish();
        reject("{{_('Error occurred')}}");
      });
    })
  }
}

{% endautoescape %}
