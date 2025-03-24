{% autoescape true %}

class PackageUI {
  constructor(type) {
    this.type = type;
    this.packages = [];
    this.initialize();
  }

  initialize() {
    $("#del_finished").click(() => this.deleteFinished());
    $("#restart_failed").click(() => this.restartFailed());
    this.parsePackages();
  }

  parsePackages() {
    const $packageList = $("#package-list");
    $packageList.children("li").each((_, ele) => {
      const id = ele.id.match(/[0-9]+/);
      this.packages.push(new Package(this, id, ele));
    });

    $packageList.sortable({
      handle: ".progress",
      axis: "y",
      cursor: "grabbing",
      start(event, ui) {
        $(this).attr('data-previndex', ui.item.index());
      },
      stop(event, ui) {
        const newIndex = ui.item.index();
        const oldIndex = $(this).attr('data-previndex');
        $(this).removeAttr('data-previndex');
        if (newIndex === oldIndex) {
          return false;
        }
        indicateLoad();
        $.get({
          url: "{{url_for('json.package_order')}}",
          data: { pid: ui.item.data('pid'), pos: newIndex },
          traditional: true,
          success: () => {
            indicateFinish();
            return true;
          }
        }).fail(() => {
          indicateFail();
          return false;
        });
      }
    });
  }

  deleteFinished() {
    indicateLoad();
    $.get("{{url_for('api.rpc', func='delete_finished')}}")
      .done((data) => {
        if (data.length > 0) {
          window.location.reload();
        } else {
          this.packages.forEach(pack => pack.close());
        }
        indicateSuccess();
      })
      .fail(() => {
        indicateFail();
      });
  }

  restartFailed() {
    indicateLoad();
    $.get("{{url_for('api.rpc', func='restart_failed')}}")
      .done((data) => {
        if (data.length > 0) {
          this.packages.forEach(pack => pack.close());
        }
        indicateSuccess();
      })
      .fail(() => {
        indicateFail();
      });
  }
}

class Package {
  constructor(ui, id, ele) {
    this.ui = ui;
    this.id = id;
    this.ele = ele;
    this.linksLoaded = false;
    this.initialize();
  }

  initialize() {
    if (!this.ele) {
      this.createElement();
    } else {
      jQuery.data(this.ele, "pid", this.id);
      this.parseElement();
    }

    const pname = $(this.ele).find('.packagename');
    this.buttons = $(this.ele).find('.buttons');
    this.buttons.css("opacity", 0);

    $(pname).hover(
      () => this.buttons.fadeTo('fast', 1),
      () => this.buttons.fadeTo('fast', 0)
    );
  }

  createElement() {
    alert("create");
  }

  parseElement() {
    const imgs = $(this.ele).find('span');
    this.name = $(this.ele).find('.name');
    this.folder = $(this.ele).find('.folder');
    this.password = $(this.ele).find('.password');

    $(imgs[3]).click(() => this.deletePackage());
    $(imgs[4]).click(() => this.restartPackage());
    $(imgs[5]).click(() => this.editPackage());
    $(imgs[6]).click(() => this.movePackage());
    $(imgs[7]).click(() => this.editOrder());
    $(imgs[8]).click(() => this.extractPackage());

    $(this.ele).find('.packagename').click(() => this.toggle());
  }

  loadLinks() {
    indicateLoad();
    $.get({
      url: "{{url_for('json.package')}}",
      data: { id: this.id },
      traditional: true
    })
      .done((data) => {
        this.createLinks(data);
      })
      .fail(() => {
        indicateFail();
      });
  }

  createLinks(data) {
    const ul = $(`#sort_children_${this.id[0]}`);
    ul.html("");
    data.links.forEach(link => {
      link.id = link.fid;
      const li = document.createElement("li");
      $(li).css("margin-left", 0);

      link.icon = this.getLinkIcon(link.status);

      const html = `
        <span class='child_status'>
          <span style='margin-right: 2px;color: #f9be03;' class='${link.icon}'></span>
          </span>
          <span style='font-size: 16px; font-weight: bold;'>
            <a onclick='return false' href='${link.url}'>${link.name}</a>
          </span><br/>
          <div class='child_secrow' style='margin-left: 21px; margin-bottom: 7px; border-radius: 4px;'>
            <span class='child_status' style='font-size: 12px; color:#eee; padding-left: 5px;'>${link.statusmsg}</span>&nbsp;${link.error}&nbsp;
            <span class='child_status' style='font-size: 12px; color:#eee;'>${link.format_size}</span>
            <span class='child_status' style='font-size: 12px; color:#eee;'> ${link.plugin}</span>&nbsp;&nbsp;
            <span class='glyphicon glyphicon-trash' title='{{_('Delete Link')}}' style='cursor: pointer;  font-size: 12px; color:#eee;'></span>&nbsp;&nbsp;
            <span class='glyphicon glyphicon-repeat' title='{{_('Restart Link')}}' style='cursor: pointer; font-size: 12px; color:#eee;'></span>
          </div>`;

      const div = document.createElement("div");
      $(div).attr("id", `file_${link.id}`);
      $(div).css("padding-left", "30px");
      $(div).css("cursor", "grab");
      $(div).addClass("child");
      $(div).html(html);

      jQuery.data(li, "lid", link.id);
      li.appendChild(div);
      ul[0].appendChild(li);
    });

    this.registerLinkEvents();
    this.linksLoaded = true;
    indicateFinish();
    this.toggle();
  }

  getLinkIcon(status) {
    switch (status) {
      case 0:
        return 'glyphicon glyphicon-ok';
      case 2:
      case 3:
      case 5:
        return 'glyphicon glyphicon-time';
      case 9:
      case 1:
        return 'glyphicon glyphicon-ban-circle';
      case 8:
        return 'glyphicon glyphicon-exclamation-sign';
      case 4:
        return 'glyphicon glyphicon-arrow-right';
      case 11:
      case 13:
        return 'glyphicon glyphicon-cog';
      default:
        return 'glyphicon glyphicon-cloud-download';
    }
  }

  registerLinkEvents() {
    $(this.ele).find('.children').children('ul').children("li").each((_, child) => {
      const lid = $(child).find('.child').attr('id').match(/[0-9]+/);
      const imgs = $(child).find('.child_secrow span');
      $(imgs[3]).click(() => this.deleteLink(lid));
      $(imgs[4]).click(() => this.restartLink(lid));
    });

    $(this.ele).find('.children').children('ul').sortable({
      handle: ".child",
      axis: "y",
      cursor: "grabbing",
      start(e, ui) {
        $(this).attr('data-previndex', ui.item.index());
      },
      stop(event, ui) {
        const newIndex = ui.item.index();
        const oldIndex = $(this).attr('data-previndex');
        $(this).removeAttr('data-previndex');
        if (newIndex === oldIndex) {
          return false;
        }
        indicateLoad();
        $.get({
          url: "{{url_for('json.link_order')}}",
          data: { fid: ui.item.data('lid'), pos: newIndex },
          traditional: true,
          success: () => {
            indicateFinish();
            return true;
          }
        }).fail(() => {
          indicateFail();
          return false;
        });
      }
    });
  }

  deleteLink(lid) {
    yesNoDialog("{{_('Are you sure you want to delete this link?')}}", (answer) => {
      if (answer) {
        indicateLoad();
        $.get(`{{url_for('api.rpc', func='delete_files')}}/[${lid}]`)
          .done(() => {
            $(`#file_${lid}`).remove();
            indicateFinish();
          })
          .fail(() => {
            indicateFail();
          });
      }
    });
  }

  restartLink(lid) {
    $.get(`{{url_for('api.rpc', func='restart_file')}}/${lid}`)
      .done(() => {
        const ele1 = $(`#file_${lid}`);
        const imgs1 = $(ele1).find(".glyphicon");
        $(imgs1[0]).attr("class", "glyphicon glyphicon-time text-info");
        const spans = $(ele1).find(".child_status");
        $(spans[1]).html("{{_('queued')}}");
        indicateSuccess();
      })
      .fail(() => {
        indicateFail();
      });
  }

  toggle() {
    const icon = $(this.ele).find('.packageicon');
    const child = $(this.ele).find('.children');
    if (child.css('display') === "block") {
      $(child).fadeOut();
      icon.removeClass('glyphicon-folder-open');
      icon.addClass('glyphicon-folder-close');
    } else {
      if (!this.linksLoaded) {
        this.loadLinks();
      } else {
        $(child).fadeIn();
      }
      icon.removeClass('glyphicon-folder-close');
      icon.addClass('glyphicon-folder-open');
    }
  }

  deletePackage() {
    yesNoDialog("{{_('Are you sure you want to delete this package?')}}", (answer) => {
      if (answer) {
        indicateLoad();
        $.get(`{{url_for('api.rpc', func='delete_packages')}}/[${this.id}]`)
          .done(() => {
            $(this.ele).remove();
            indicateFinish();
          })
          .fail(() => {
            indicateFail();
          });
      }
    });
  }

  restartPackage() {
    indicateLoad();
    $.get(`{{url_for('api.rpc', func='restart_package')}}/${this.id}`)
      .done(() => {
        this.close();
        indicateSuccess();
      })
      .fail(() => {
        indicateFail();
      });
  }

  extractPackage() {
    indicateLoad();
    $.get(`{{url_for('api.rpc', func='service_call')}}/'ExtractArchive.extract_package', [${this.id}]`)
      .done(() => {
        this.close();
        indicateSuccess();
      })
      .fail(() => {
        indicateFail();
      });
  }

  close() {
    const child = $(this.ele).find('.children');
    if (child.css('display') === "block") {
      child.fadeOut();
      const icon = $(this.ele).find('.packageicon');
      icon.removeClass('glyphicon-folder-open');
      icon.addClass('glyphicon-folder-close');
    }
    const ul = $(`#sort_children_${this.id}`);
    ul.html("");
    this.linksLoaded = false;
  }

  movePackage() {
    indicateLoad();
    $.get({
      url: "{{url_for('json.move_package')}}",
      data: { id: this.id, dest: ((this.ui.type + 1) % 2) },
      traditional: true
    })
      .done(() => {
        $(this.ele).remove();
        indicateFinish();
      })
      .fail(() => {
        indicateFail();
      });
  }

  editOrder() {
    indicateLoad();
    $.get({
      url: "{{url_for('json.package')}}",
      data: {id: this.id},
      traditional: true
    })
      .done((data) => {
        const length = data.links.length;
        for (let i = 1; i <= length / 2; i++) {
          $.get({
            url: "{{url_for('json.link_order')}}",
            data: { fid: data.links[length - i].fid, pos: i - 1 },
            traditional: true
          }).fail(() => {
            indicateFail();
          });
        }
        indicateFinish();
        this.close();
      })
      .fail(() => {
        indicateFail();
      });
  }

  editPackage(event) {
    event.stopPropagation();
    event.preventDefault();
    $("#pack_form").off("submit").submit((e) => this.savePackage(e));

    $("#pack_id").val(this.id[0]);
    $("#pack_name").val(this.name.text());
    $("#pack_folder").val(this.folder.text());
    $("#pack_pws").val(this.password.text());
    $('#pack_box').modal('show');
  }

  savePackage(event) {
    $.ajax({
      url: "{{url_for('json.edit_package')}}",
      type: 'post',
      dataType: 'json',
      data: $('#pack_form').serialize()
    });
    event.preventDefault();
    this.name.text($("#pack_name").val());
    this.folder.text($("#pack_folder").val());
    this.password.text($("#pack_pws").val());
    $('#pack_box').modal('hide');
  }
}

{% endautoescape %}
