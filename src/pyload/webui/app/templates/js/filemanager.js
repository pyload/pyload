{% autoescape true %}

var load, rename_box, confirm_box;

document.addEvent("domready", function() {
    load = new Fx.Tween($("load-indicator"), {link: "cancel"});
    load.set("opacity", 0);

    rename_box = new Fx.Tween($('rename_box'));
    confirm_box = new Fx.Tween($('confirm_box'));
    $('rename_reset').addEvent('click', function() {
        hide_rename_box()
    });
    $('delete_reset').addEvent('click', function() {
        hide_confirm_box()
    });

    var fmUI = new FilemanagerUI("url", 1);

    /*$('filemanager_actions_list').getChildren("li").each(function(action) {
        var action_name = action.className;
        if(functions[action.className] != undefined)
        {
            action.addEvent('click', functions[action.className]);
        }
    });*/
});

function indicateLoad() {
    //$("load-indicator").reveal();
    load.start("opacity", 1)
}

function indicateFinish() {
    load.start("opacity", 0)
}

function indicateSuccess() {
    indicateFinish();
    notify.alert('{{_("Success")}}', {
             'className': 'success'
    });
}

function indicateFail() {
    indicateFinish();
    notify.alert('{{_("Failed")}}', {
             'className': 'error'
    });
}

function show_rename_box() {
    bg_show();
    $("rename_box").setStyle('display', 'block');
    rename_box.start('opacity', 1)
}

function hide_rename_box() {
    bg_hide();
    rename_box.start('opacity', 0).chain(function() {
        $('rename_box').setStyle('display', 'none');
    });
}

function show_confirm_box() {
    bg_show();
    $("confirm_box").setStyle('display', 'block');
    confirm_box.start('opacity', 1)
}

function hide_confirm_box() {
    bg_hide();
    confirm_box.start('opacity', 0).chain(function() {
        $('confirm_box').setStyle('display', 'none');
    });
}

var FilemanagerUI = new Class({
    initialize: function(url, type) {
        this.url = url;
        this.type = type;
        this.directories = [];
        this.files = [];
        this.parseChildren();
    },

    parseChildren: function() {
        $("directories-list").getChildren("li.folder").each(function(ele) {
            var path = ele.getElements("input.path")[0].get("value");
            var name = ele.getElements("input.name")[0].get("value");
            this.directories.push(new Item(this, path, name, ele))
        }.bind(this));

    $("directories-list").getChildren("li.file").each(function(ele) {
            var path = ele.getElements("input.path")[0].get("value");
            var name = ele.getElements("input.name")[0].get("value");
            this.files.push(new Item(this, path, name, ele))
        }.bind(this));
    }
});

var Item = new Class({
    initialize: function(ui, path, name, ele) {
        this.ui = ui;
        this.path = path;
        this.name = name;
        this.ele = ele;
        this.directories = [];
        this.files = [];
        this.actions = [];
        this.actions["delete"] = this.del;
        this.actions.rename = this.rename;
        this.actions.mkdir = this.mkdir;
        this.parseElement();

        var pname = this.ele.getElements("span")[0];
        this.buttons = new Fx.Tween(this.ele.getElements(".buttons")[0], {link: "cancel"});
        this.buttons.set("opacity", 0);

        pname.addEvent("mouseenter", function(e) {
            this.buttons.start("opacity", 1)
        }.bind(this));

        pname.addEvent("mouseleave", function(e) {
            this.buttons.start("opacity", 0)
        }.bind(this));

    },

    parseElement: function() {
        this.ele.getChildren('span span.buttons img').each(function(img) {
            img.addEvent('click', this.actions[img.className].bind(this));
    }, this);

    //click on the directory name must open the directory itself
    this.ele.getElements('b')[0].addEvent('click', this.toggle.bind(this));

    //iterate over child directories
    var uls = this.ele.getElements('ul');
    if(uls.length > 0)
    {
        uls[0].getChildren("li.folder").each(function(fld) {
            var path = fld.getElements("input.path")[0].get("value");
            var name = fld.getElements("input.name")[0].get("value");
            this.directories.push(new Item(this, path, name, fld));
        }.bind(this));
        uls[0].getChildren("li.file").each(function(fld) {
            var path = fld.getElements("input.path")[0].get("value");
            var name = fld.getElements("input.name")[0].get("value");
            this.files.push(new Item(this, path, name, fld));
        }.bind(this));
    }
    },

    reorderElements: function() {
      //TODO: sort the main ul again (to keep data ordered after renaming something)
    },

    del: function(event) {
        $("confirm_form").removeEvents("submit");
        $("confirm_form").addEvent("submit", this.deleteDirectory.bind(this));

        $$("#confirm_form p").set('html', '{{_(("Are you sure you want to delete the selected item?"))}}');

        show_confirm_box();
        event.stop();
    },

    deleteDirectory: function(event) {
        hide_confirm_box();
        new Request.JSON({
            method: 'POST',
            url: "{{url_for('json.filemanager_delete')}}",
            data: {"path": this.path, "name": this.name},
            onSuccess: function(data) {
                if(data.response == "success")
                {
                    new Fx.Tween(this.ele).start('opacity', 0);
                    var ul = this.ele.parentNode;
                    this.ele.dispose();
                    //if this was the only child, add a "empty folder" div
                    if(!ul.getChildren('li')[0])
                    {
                        var div = new Element("div", { 'html': '{{ _("Folder is empty") }}' });
                        div.replaces(ul);
                    }

                    indicateSuccess();
                } else {
                    //error from json code...
                    indicateFail();
                }
            }.bind(this),
            onFailure: indicateFail
        }).send();

        event.stop();
    },

    rename: function(event) {
        $("rename_form").removeEvents("submit");
        $("rename_form").addEvent("submit", this.renameDirectory.bind(this));

        $("path").set("value", this.path);
        $("old_name").set("value", this.name);
        $("new_name").set("value", this.name);

        show_rename_box();
        event.stop();
    },

    renameDirectory: function(event) {
        hide_rename_box();
        new Request.JSON({
            method: 'POST',
            url: "{{url_for('json.filemanager_rename')}}",
            onSuccess: function(data) {
                if(data.response == "success")
                {
                    this.name = $("new_name").get("value");
                    this.ele.getElements("b")[0].set('html', $("new_name").get("value"));
                    this.reorderElements();
                    indicateSuccess();
                } else {
                    //error from json code...
                    indicateFail();
                }
            }.bind(this),
            onFailure: indicateFail
        }).send($("rename_form").toQueryString());

        event.stop();
    },

    mkdir: function(event) {
        new Request.JSON({
            method: 'POST',
            url: "{{url_for('json.filemanager_mkdir')}}",
            data: {"path": this.path + "/" + this.name, "name": '{{_("New folder")}}'},
            onSuccess: function(data) {
                if(data.response == "success") {
                    new Request.HTML({
                        method: 'POST',
                        url: "{{url_for('json.filemanager_get_dir')}}",
                        data: {"path": data.path, "name": data.name},
                        onSuccess: function(li) {
                            //add node as first child of ul
                            var ul = this.ele.getChildren('ul')[0];
                            if(!ul)
                            {
                                //remove the "Folder Empty" div
                                this.ele.getChildren('div').dispose();

                                //create new ul to contain subfolder
                                ul = new Element("ul");
                                ul.inject(this.ele, 'bottom');
                            }
                            li[0].inject(ul, 'top');

                            //add directory as a subdirectory of the current item
                            this.directories.push(new Item(this.ui, data.path, data.name, ul.firstChild));
                        }.bind(this),
                        onFailure: indicateFail
                    }).send();
                    indicateSuccess();
                } else {
                    //error from json code...
                    indicateFail();
                }
            }.bind(this),
            onFailure: indicateFail
        }).send();

        event.stop();
    },

    toggle: function() {
        var child = this.ele.getElement('ul');
        if (child == null) {
            child = this.ele.getElement('div');
        }

        if(child != null)
        {
            if (child.getStyle('display') == "block") {
                child.dissolve();
            } else {
                child.reveal();
            }
        }
    }
});

{% endautoescape %}
