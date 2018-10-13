var root = this;

document.addEvent("domready", function() {
    root.load = new Fx.Tween($("load-indicator"), {link: "cancel"});
    root.load.set("opacity", 0);


    root.packageBox = new MooDialog({destroyOnHide: false});
    root.packageBox.setContent($('pack_box'));

    $('pack_reset').addEvent('click', function() {
        $('pack_form').reset();
        root.packageBox.close();
    });
});

function indicateLoad() {
    //$("load-indicator").reveal();
    root.load.start("opacity", 1)
}

function indicateFinish() {
    root.load.start("opacity", 0)
}

function indicateSuccess() {
    indicateFinish();
    root.notify.alert('{{_("Success")}}.', {
             'className': 'success'
    });
}

function indicateFail() {
    indicateFinish();
    root.notify.alert('{{_("Failed")}}.', {
             'className': 'error'
    });
}

var PackageUI = new Class({
    initialize: function(url, type) {
        this.url = url;
        this.type = type;
        this.packages = [];
        this.parsePackages();

        this.sorts = new Sortables($("package-list"), {
            constrain: false,
            clone: true,
            revert: true,
            opacity: 0.4,
            handle: ".package_drag",
            onComplete: this.saveSort.bind(this)
        });

        $("del_finished").addEvent("click", this.deleteFinished.bind(this));
        $("restart_failed").addEvent("click", this.restartFailed.bind(this));

    },

    parsePackages: function() {
        $("package-list").getChildren("li").each(function(ele) {
            var id = ele.getFirst().get("id").match(/[0-9]+/);
            this.packages.push(new Package(this, id, ele))
        }.bind(this))
    },

    loadPackages: function() {
    },

    deleteFinished: function() {
        indicateLoad();
        new Request.JSON({
            method: 'get',
            url: '/api/deleteFinished',
            onSuccess: function(data) {
                if (data.length > 0) {
                    window.location.reload()
                } else {
                    this.packages.each(function(pack) {
                        pack.close();
                    });
                    indicateSuccess();
                }
            }.bind(this),
            onFailure: indicateFail
        }).send();
    },

    restartFailed: function() {
        indicateLoad();
        new Request.JSON({
            method: 'get',
            url: '/api/restartFailed',
            onSuccess: function(data) {
                this.packages.each(function(pack) {
                    pack.close();
                });
                indicateSuccess();
            }.bind(this),
            onFailure: indicateFail
        }).send();
    },

    startSort: function(ele, copy) {
    },

    saveSort: function(ele, copy) {
        var order = [];
        this.sorts.serialize(function(li, pos) {
            if (li == ele && ele.retrieve("order") != pos) {
                order.push(ele.retrieve("pid") + "|" + pos)
            }
            li.store("order", pos)
        });
        if (order.length > 0) {
            indicateLoad();
            new Request.JSON({
                method: 'get',
                url: '/json/package_order/' + order[0],
                onSuccess: indicateFinish,
                onFailure: indicateFail
            }).send();
        }
    }

});

var Package = new Class({
    initialize: function(ui, id, ele, data) {
        this.ui = ui;
        this.id = id;
        this.linksLoaded = false;

        if (!ele) {
            this.createElement(data);
        } else {
            this.ele = ele;
            this.order = ele.getElements("div.order")[0].get("html");
            this.ele.store("order", this.order);
            this.ele.store("pid", this.id);
            this.parseElement();
        }

        var pname = this.ele.getElements(".packagename")[0];
        this.buttons = new Fx.Tween(this.ele.getElements(".buttons")[0], {link: "cancel"});
        this.buttons.set("opacity", 0);

        pname.addEvent("mouseenter", function(e) {
            this.buttons.start("opacity", 1)
        }.bind(this));

        pname.addEvent("mouseleave", function(e) {
            this.buttons.start("opacity", 0)
        }.bind(this));


    },

    createElement: function() {
        alert("create")
    },

    parseElement: function() {
        var imgs = this.ele.getElements('span');

        this.name = this.ele.getElements('.name')[0];
        this.folder = this.ele.getElements('.folder')[0];
        this.password = this.ele.getElements('.password')[0];

        imgs[3].addEvent('click', this.deletePackage.bind(this));
        imgs[4].addEvent('click', this.restartPackage.bind(this));
        imgs[5].addEvent('click', this.editPackage.bind(this));
        imgs[6].addEvent('click', this.movePackage.bind(this));

        this.ele.getElement('.packagename').addEvent('click', this.toggle.bind(this));

    },

    loadLinks: function() {
        indicateLoad();
        new Request.JSON({
            method: 'get',
            url: '/json/package/' + this.id,
            onSuccess: this.createLinks.bind(this),
            onFailure: indicateFail
        }).send();
    },

    createLinks: function(data) {
        var ul = $("sort_children_{id}".substitute({"id": this.id}));
        ul.set("html", "");
        data.links.each(function(link) {
            link.id = link.fid;
            var li = new Element("li", {
                "style": {
                    "margin-left": 0
                }
            });

            if (link.icon == 'arrow_right.png'){
                    link.icon = 'glyphicon glyphicon-arrow-right';
            }
            if (link.icon == 'status_downloading.png'){
                    link.icon = 'glyphicon glyphicon-cloud-download';
            }
            if (link.icon == 'status_failed.png'){
                    link.icon = 'glyphicon glyphicon-exclamation-sign';
            }
            if (link.icon == 'status_finished.png'){
                    link.icon = 'glyphicon glyphicon-ok';
            }
            if (link.statusmsg == 'queued'){
                    link.icon = 'glyphicon glyphicon-time';
            }
            if (link.icon == 'status_offline.png'){
                    link.icon = 'glyphicon glyphicon-ban-circle';
            }


            var html = "<span style='' class='child_status'><span style='margin-right: 2px;' class='{icon} sorthandle'></span></span>\n".substitute({"icon": link.icon});
            html += "<span style='font-size: 18px; text-weight:bold'>{name}</span><br /><div class='child_secrow' style='margin-left: 21px; margin-bottom: 7px;'>".substitute({"name": link.name});
            html += "<span class='child_status' style='font-size: 12px; color:#555'>{statusmsg}</span>{error}&nbsp;".substitute({"statusmsg": link.statusmsg, "error":link.error});
            html += "<span class='child_status' style='font-size: 12px; color:#555'>{format_size}</span>".substitute({"format_size": link.format_size});
            html += "<span class='child_status' style='font-size: 12px; color:#555'> {plugin}</span>&nbsp;&nbsp;".substitute({"plugin": link.plugin});
            html += "<span class='glyphicon glyphicon-trash' title='{{_("Delete Link")}}' style='cursor: pointer;  font-size: 12px; color:#333;' ></span>&nbsp;&nbsp;";
            html += "<span class='glyphicon glyphicon-repeat' title='{{_("Restart Link")}}' style='cursor: pointer; font-size: 12px; color:#333;' ></span></div>";

            var div = new Element("div", {
                "id": "file_" + link.id,
                "class": "child",
                "html": html
            });

            li.store("order", link.order);
            li.store("lid", link.id);

            li.adopt(div);
            ul.adopt(li);
        });
        this.sorts = new Sortables(ul, {
            constrain: false,
            clone: true,
            revert: true,
            opacity: 0.4,
            handle: ".sorthandle",
            onComplete: this.saveSort.bind(this)
        });
        this.registerLinkEvents();
        this.linksLoaded = true;
        indicateFinish();
        this.toggle();
    },

    registerLinkEvents: function() {
        this.ele.getElements('.child').each(function(child) {
            var lid = child.get('id').match(/[0-9]+/);
            var imgs = child.getElements('.child_secrow span');
            imgs[3].addEvent('click', function(e) {
                new Request({
                    method: 'get',
                    url: '/api/deleteFiles/[' + this + "]",
                    onSuccess: function() {
                        $('file_' + this).nix()
                    }.bind(this),
                    onFailure: indicateFail
                }).send();
            }.bind(lid));

            imgs[4].addEvent('click', function(e) {
                new Request({
                    method: 'get',
                    url: '/api/restartFile/' + this,
                    onSuccess: function() {
                        var ele = $('file_' + this);
                        var imgs = ele.getElements(".glyphicon");
                        imgs[0].set("class", "glyphicon glyphicon-time");
                        var spans = ele.getElements(".child_status");
                        spans[1].set("html", "queued");
                        indicateSuccess();
                    }.bind(this),
                    onFailure: indicateFail
                }).send();
            }.bind(lid));
        });
    },

    toggle: function() {
        var child = this.ele.getElement('.children');
        if (child.getStyle('display') == "block") {
            child.dissolve();
        } else {
            if (!this.linksLoaded) {
                this.loadLinks();
            } else {
                child.reveal();
            }
        }
    },


    deletePackage: function(event) {
        indicateLoad();
        new Request({
            method: 'get',
            url: '/api/deletePackages/[' + this.id + "]",
            onSuccess: function() {
                this.ele.nix();
                indicateFinish();
            }.bind(this),
            onFailure: indicateFail
        }).send();
        //hide_pack();
        event.stop();
    },

    restartPackage: function(event) {
        indicateLoad();
        new Request({
            method: 'get',
            url: '/api/restartPackage/' + this.id,
            onSuccess: function() {
                this.close();
                indicateSuccess();
            }.bind(this),
            onFailure: indicateFail
        }).send();
        event.stop();
    },

    close: function() {
        var child = this.ele.getElement('.children');
        if (child.getStyle('display') == "block") {
            child.dissolve();
        }
        var ul = $("sort_children_{id}".substitute({"id": this.id}));
        ul.erase("html");
        this.linksLoaded = false;
    },

    movePackage: function(event) {
        indicateLoad();
        new Request({
            method: 'get',
            url: '/json/move_package/' + ((this.ui.type + 1) % 2) + "/" + this.id,
            onSuccess: function() {
                this.ele.nix();
                indicateFinish();
            }.bind(this),
            onFailure: indicateFail
        }).send();
        event.stop();
    },

    editPackage: function(event) {
        $("pack_form").removeEvents("submit");
        $("pack_form").addEvent("submit", this.savePackage.bind(this));

        $("pack_id").set("value", this.id);
        $("pack_name").set("value", this.name.get("text"));
        $("pack_folder").set("value", this.folder.get("text"));
        $("pack_pws").set("value", this.password.get("text"));

        root.packageBox.open();
        event.stop();
    },

    savePackage: function(event) {
        $("pack_form").send();
        this.name.set("text", $("pack_name").get("value"));
        this.folder.set("text", $("pack_folder").get("value"));
        this.password.set("text", $("pack_pws").get("value"));
        root.packageBox.close();
        event.stop();
    },

    saveSort: function(ele, copy) {
        var order = [];
        this.sorts.serialize(function(li, pos) {
            if (li == ele && ele.retrieve("order") != pos) {
                order.push(ele.retrieve("lid") + "|" + pos)
            }
            li.store("order", pos)
        });
        if (order.length > 0) {
            indicateLoad();
            new Request.JSON({
                method: 'get',
                url: '/json/link_order/' + order[0],
                onSuccess: indicateFinish,
                onFailure: indicateFail
            }).send();
        }
    }

});

