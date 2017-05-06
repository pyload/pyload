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
        var imgs = this.ele.getElements('img');

        this.name = this.ele.getElements('.name')[0];
        this.folder = this.ele.getElements('.folder')[0];
        this.password = this.ele.getElements('.password')[0];

        imgs[1].addEvent('click', this.deletePackage.bind(this));
        imgs[2].addEvent('click', this.restartPackage.bind(this));
        imgs[3].addEvent('click', this.editPackage.bind(this));
        imgs[4].addEvent('click', this.movePackage.bind(this));

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

    deleteLinkByType: function(type) {

        var ul = $("sort_children_{id}".substitute({"id": this.id}));

        switch (type) {
            case "all":
            case "none":
                ul.getElements('input[name="delete_bundle"]').each(function(el) {
                    el.checked = "all" == type;
                    $$(el).fireEvent("change");
                });
                break;
            default:
                ul.getElements('.link_plugin_name').each(function(el) {
                    if (type == $$(el).get("text").toString()) {
                        var checkbox = $$(el).getParent().getElement('input[name="delete_bundle"]');

                        checkbox[0].checked = true;
                        checkbox[0].fireEvent("change");
                    }
                });
        }
    },

    createLinks: function(data) {
        var children = $("children_{id}".substitute({"id": this.id}));
        var ul = $("sort_children_{id}".substitute({"id": this.id}));
        ul.set("html", "");

        var packageObject = this;

        var selectionElements = new Element("div", {id: "selection_elements"});
        var markDropdown = new Element("select", {
            id:"select_mark"

        }).addEvent('change',function() {
            if (this.getSelected().get("value")) {
                packageObject.deleteLinkByType(this.getSelected().get("value").toString());
            }
        });

        new Element('option', {'text':'Select...'}).inject(markDropdown);
        new Element('option', {'value': 'all', 'text':'All'}).inject(markDropdown);
        new Element('option', {'value': 'none', 'text':'None'}).inject(markDropdown);


        selectionElements.adopt(markDropdown).inject(ul, "before");

        var downloadPlugins = {};
        data.links.each(function(link) {

            downloadPlugins[link.plugin] = downloadPlugins[link.plugin] || [];
            downloadPlugins[link.plugin].push(link.fid);

            link.id = link.fid;
            var li = new Element("li", {
                "style": {
                    "margin-left": 0
                }
            });


            var html = "<span style='cursor: move' class='child_status sorthandle'><img src='/media/default/img/{icon}' style='width: 12px; height:12px;'/></span>\n".substitute({"icon": link.icon});
            html += "<span style='font-size: 15px'>{name}</span><br /><div class='child_secrow'>".substitute({"name": link.name});
            html += "<span class='child_status'>{statusmsg}</span>{error}&nbsp;".substitute({"statusmsg": link.statusmsg, "error":link.error});
            html += "<span class='child_status'>{format_size}</span>".substitute({"format_size": link.format_size});
            html += "<span class='child_status link_plugin_name'>{plugin}</span>&nbsp;&nbsp;".substitute({"plugin": link.plugin});
            html += "<input type='checkbox' name='delete_bundle' value='1' />";
            html += "<img title='{{_("Delete Link")}}' style='cursor: pointer;' width='10px' height='10px' src='/media/default/img/delete.png' />&nbsp;&nbsp;";
            html += "<img title='{{_("Restart Link")}}' style='cursor: pointer;margin-left: -4px' width='10px' height='10px' src='/media/default/img/arrow_refresh.png' /></div>";

            var div = new Element("div", {
                "id": "file_" + link.id,
                "class": "child",
                "html": html
            });

            div.getElement('input[name="delete_bundle"]').addEvent("change", function() {
                if (0 < ul.getElements('input[name="delete_bundle"]:checked').length) {

                    if (!children.getElement("button.delete_bundle")) {
                        var deleteButton = new Element("button", {
                            html: "Delete chosen",
                            class: "delete_bundle"
                        }).addEvent("click", function () {
                                packageObject.bundleDelete();
                            });

                        selectionElements.adopt(deleteButton);
                    }
                } else if (deleteButton = selectionElements.getElement("button.delete_bundle")) {
                    deleteButton.remove();
                }
            });

            li.store("order", link.order);
            li.store("lid", link.id);

            li.adopt(div);
            ul.adopt(li);
        });

        Object.each(downloadPlugins, function(lids, pluginName, el) {

            var button = new Element("option", {
                text: pluginName,
                value: pluginName
            })
            .inject(markDropdown)
            .addEvent("click", function() {
                lids.each(function(lid) {
                    var linkElement = $("file_{lid}".substitute({lid: lid})).getElement("input[name='delete_bundle']");
                    linkElement.checked = "checked";
                    $$(linkElement).fireEvent("change");
                })
            });
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

    bundleDelete: function() {
        var $toDelete = $$("#" + this.id.input).getElements('input[name="delete_bundle"]:checked');

        var linkIds = [];
        $toDelete.each(function(elem) {
            var lid = elem.getParent("li").retrieve("lid");
            linkIds.push(lid);
        });

        linkIds.getLast().each(function(linkId) {
            new Request({
                    method: 'get',
                    url: '/api/deleteFiles/[' + linkId + "]",
                    onSuccess: function() {
                        $('file_' + linkId).nix()
                    },
                    onFailure: indicateFail
                }).send();
        });

        if (!$$("#" + this.id.input).getElements('input[name="delete_bundle"]').length) {
            this.deletePackage();
        }

    },

    registerLinkEvents: function() {

        this.ele.getElements('.child').each(function(child) {
            var lid = child.get('id').match(/[0-9]+/);

            var imgs = child.getElements('.child_secrow img');
            imgs[0].addEvent('click', function(e) {
                new Request({
                    method: 'get',
                    url: '/api/deleteFiles/[' + this + "]",
                    onSuccess: function() {
                        $('file_' + this).nix()
                    }.bind(this),
                    onFailure: indicateFail
                }).send();
            }.bind(lid));

            imgs[1].addEvent('click', function(e) {
                new Request({
                    method: 'get',
                    url: '/api/restartFile/' + this,
                    onSuccess: function() {
                        var ele = $('file_' + this);
                        var imgs = ele.getElements("img");
                        imgs[0].set("src", "/media/default/img/status_queue.png");
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

        if (event) {
            event.stop();
        }
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

