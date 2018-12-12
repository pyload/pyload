var root = this;

function PackageUI (url, type){
    var packages = [];
    var thisObject;
    this.initialize = function(url, type) {
        thisObject = this;
        this.url = url;
        this.type = type;

        $("#del_finished").click(this.deleteFinished);
        $("#restart_failed").click(this.restartFailed);
        this.parsePackages();

    };

    this.parsePackages = function () {
       $("#package-list")
           .children("li").each(function(ele) {
               var id = this.id.match(/[0-9]+/);
               packages.push(new Package(thisObject, id, this));
           })
           .sortable({
               handle: ".progress",
               axis: "y",
               cursor: "grabbing",
               start: function(e, ui) {
                   $(this).attr('data-previndex', ui.item.index());
               },
               stop: function(event, ui) {
                   var newIndex = ui.item.index();
                   var oldIndex = $(this).attr('data-previndex');
                   $(this).removeAttr('data-previndex');
                   if (newIndex === oldIndex) {
                       return false;
                   }
                   var order = ui.item.data('pid') + '|' + newIndex;
                   indicateLoad();
                   $.get("{{'/json/package_order/'|url}}" + order, function () {
                       indicateFinish();
                       return true;
                   }).fail(function () {
                       indicateFail();
                       return false;
                   });
               }
           });
    };

    this.deleteFinished = function () {
        indicateLoad();
        $.get("{{'/api/deleteFinished'|url}}", function(data) {
            if (data.length > 0) {
                window.location.reload();
            } else {
                $.each(packages, function (pack) {
                    this.close();
                });
            }
            indicateSuccess();
        }).fail(function () {
            indicateFail();
        });
    };

    this.restartFailed = function () {
        indicateLoad();
        $.get( "{{'/api/restartFailed'|url}}", function(data) {
            if (data.length > 0) {
                $.each(packages,function(pack) {
                    this.close();
                });
            }
            indicateSuccess();
        }).fail(function () {
            indicateFail();
        });
    };

    this.initialize(url, type);
}

function Package (ui, id, ele){
    // private variables
    var linksLoaded = false;
    var thisObject;
    var buttons;
    var name;
    var password;
    var folder;

    this.initialize = function () {
        thisObject = this;
        if (!ele) {
            this.createElement();
        } else {
            jQuery.data(ele,"pid", id);
            this.parseElement();
        }

        var pname = $(ele).find('.packagename');

        buttons = $(ele).find('.buttons');
        buttons.css("opacity", 0);

        $(pname).mouseenter(function(e) {
            $(this).find('.buttons').fadeTo('fast', 1)
        });

        $(pname).mouseleave( function(e) {
            $(this).find('.buttons').fadeTo('fast', 0)
        });
    };

    this.createElement = function () {
        alert("create");
    };

    this.parseElement = function () {
        var imgs = $(ele).find('span');

        name = $(ele).find('.name');
        folder =  $(ele).find('.folder');
        password = $(ele).find('.password');

        $(imgs[3]).click(this.deletePackage);
        $(imgs[4]).click(this.restartPackage);
        $(imgs[5]).click(this.editPackage);
        $(imgs[6]).click(this.movePackage);
        $(imgs[7]).click(this.editOrder);

        $(ele).find('.packagename').click(this.toggle);
    };

    this.loadLinks = function () {
        indicateLoad();
        $.get("{{'/json/package/'|url}}" + id, thisObject.createLinks)
        .fail(function () {
            indicateFail();
            return false;
        })
        .done(function() {
            return true;
        });
    };

    this.createLinks = function(data) {
        var ul = $("#sort_children_" + id[0]);
        ul.html("");
        $.each(data.links, function(key, link) {      // data.links.each(
            link.id = link.fid;
            var li = document.createElement("li");
            $(li).css("margin-left",0);

            if (link.status === 0)
                link.icon = 'glyphicon glyphicon-ok';
            else if (link.status === 2 || link.status === 3)
                link.icon = 'glyphicon glyphicon-time';
            else if (link.status ===  9 || link.status === 1)
                link.icon = 'glyphicon glyphicon-ban-circle';
            else if (link.status === 5)
                link.icon = 'glyphicon glyphicon-time';
            else if (link.status === 8)
                link.icon = 'glyphicon glyphicon-exclamation-sign';
            else if (link.status === 4)
                link.icon = 'glyphicon glyphicon-arrow-right';
            else if (link.status ===  11 || link.status === 13)
                link.icon = 'glyphicon glyphicon-cog';
            else
                link.icon = 'glyphicon glyphicon-cloud-download';

            var html = "<span class='child_status'><span style='margin-right: 2px;color: #337ab7;' class='" + link.icon + "'></span></span>\n" +
                       "<span style='font-size: 16px; font-weight: bold;'><a href='" + link.url + "'>" + link.url + "</a></span><br/>" +
                       "<div class='child_secrow' style='margin-left: 21px; margin-bottom: 7px; border-radius: 4px;'>" +
                       "<span class='child_status' style='font-size: 12px; color:#555; padding-left: 5px;'>" + link.statusmsg + "</span>&nbsp;" + link.error + "&nbsp;" +
                       "<span class='child_status' style='font-size: 12px; color:#555;'>" + link.format_size + "</span>" +
                       "<span class='child_status' style='font-size: 12px; color:#555;'> " + link.plugin + "</span>&nbsp;&nbsp;" +
                       "<span class='glyphicon glyphicon-trash' title='{{_('Delete Link')}}' style='cursor: pointer;  font-size: 12px; color:#333;' ></span>&nbsp;&nbsp;" +
                       "<span class='glyphicon glyphicon-repeat' title='{{_('Restart Link')}}' style='cursor: pointer; font-size: 12px; color:#333;' ></span></div>";

            var div = document.createElement("div");
            $(div).attr("id","file_" + link.id);
            $(div).css("padding-left", "30px");
            $(div).css("cursor", "grab");
            $(div).addClass("child");
            $(div).html(html);

            jQuery.data(li,"lid", link.id);

            li.appendChild(div);
            $(ul)[0].appendChild(li);
        });

        thisObject.registerLinkEvents();
        linksLoaded = true;
        indicateFinish();
        thisObject.toggle();
    };

    this.registerLinkEvents = function () {
        $(ele).find('.children').children('ul').children("li").each(function(child) {
            var lid = $(this).find('.child').attr('id').match(/[0-9]+/);
            var imgs = $(this).find('.child_secrow span');
            $(imgs[3]).bind('click',{ lid: lid}, function(e) {
                $.get("{{'/api/deleteFiles/['|url}}" + lid + "]", function () {
                    $('#file_' + lid).remove()
                }).fail(function () {
                    indicateFail();
                });
            });

            $(imgs[4]).bind('click',{ lid: lid},function(e) {
                $.get("{{'/api/restartFile/'|url}}" + lid, function () {
                    var ele1 = $('#file_' + lid);
                    var imgs1 = $(ele1).find(".glyphicon");
                    $(imgs1[0]).attr( "class","glyphicon glyphicon-time text-info");
                    var spans = $(ele1).find(".child_status");
                    $(spans[1]).html("{{_('queued')}}");
                    indicateSuccess();
                }).fail(function () {
                    indicateFail();                    
                });
            });
        });


        $(ele).find('.children').children('ul').sortable({
            handle: ".child",
            axis: "y",
            cursor: "grabbing",
            start: function(e, ui) {
                $(this).attr('data-previndex', ui.item.index());
            },
            stop: function(event, ui) {
                var newIndex = ui.item.index();
                var oldIndex = $(this).attr('data-previndex');
                $(this).removeAttr('data-previndex');
                if (newIndex === oldIndex) {
                    return false;
                }
                var order = ui.item.data('lid') + '|' + newIndex;
                indicateLoad();
                $.get("{{'/json/link_order/'|url}}" + order, function () {
                    indicateFinish();
                    return true;
                } ).fail(function () {
                    indicateFail();
                    return false;
                });
          }
        });
    };

    this.toggle = function () {
        var icon = $(ele).find('.packageicon');
        var child = $(ele).find('.children');
        if (child.css('display') === "block") {
            $(child).fadeOut();
            icon.removeClass('glyphicon-folder-open');
            icon.addClass('glyphicon-folder-close');
        } else {
            if (!linksLoaded) {
                if (!thisObject.loadLinks()) {
                    return;
                }
            } else {
                $(child).fadeIn();
            }
            icon.removeClass('glyphicon-folder-close');
            icon.addClass('glyphicon-folder-open');
        }
    };

    this.deletePackage = function(event) {
        indicateLoad();
        $.get("{{'/api/deletePackages/['|url}}" + id + "]", function () {
            $(ele).remove();
            indicateFinish();
        }).fail(function () {
            indicateFail();            
        });

        event.stopPropagation();
        event.preventDefault();
    };

    this.restartPackage = function(event) {
        indicateLoad();
        $.get("{{'/api/restartPackage/'|url}}" + id, function () {
            thisObject.close();
            indicateSuccess();
        }).fail(function () {
            indicateFail();            
        });
        event.stopPropagation();
        event.preventDefault();
    };

    this.close = function () {
        var child = $(ele).find('.children');
        if (child.css('display') === "block") {
            $(child).fadeOut();
            var icon = $(ele).find('.packageicon');
            icon.removeClass('glyphicon-folder-open');
            icon.addClass('glyphicon-folder-close');
        }
        var ul = $("#sort_children_" + id);
        $(ul).html("");
        linksLoaded = false;
    };

    this.movePackage = function(event) {
        indicateLoad();
        $.get("{{'/json/move_package/'|url}}" + ((ui.type + 1) % 2) + "/" + id, function () {
            $(ele).remove();
            indicateFinish();
        }).fail(function () {
            indicateFail();            
        });
        event.stopPropagation();
        event.preventDefault();
    };

    this.editOrder = function(event) {
        indicateLoad();
        $.get("{{'/json/package/'|url}}" + id, function(data){
            length = data.links.length;
            for (i = 1; i <= length/2; i++){
                order = data.links[length-i].fid + '|' + (i-1);
                $.get( "{{'/json/link_order/'|url}}" + order).fail(function () {
                    indicateFail();
                });
            }
        });
        indicateFinish();
        thisObject.close();
        event.stopPropagation();
        event.preventDefault();
    };


    this.editPackage = function(event) {
        event.stopPropagation();
        event.preventDefault();
        $("#pack_form").off("submit").submit(thisObject.savePackage);

        $("#pack_id").val(id[0]);
        $("#pack_name").val(name.text());
        $("#pack_folder").val(folder.text());
        $("#pack_pws").val(password.text());
        $('#pack_box').modal('show');
    };

    this.savePackage = function(event) {
        $.ajax({
            url: "{{'/json/edit_package'|url}}",
            type: 'post',
            dataType: 'json',
            data: $('#pack_form').serialize()
        });
        event.preventDefault();
        name.text( $("#pack_name").val());
        folder.text( $("#pack_folder").val());
        password.text($("#pack_pws").val());
        $('#pack_box').modal('hide');
    };

    this.initialize();
}

