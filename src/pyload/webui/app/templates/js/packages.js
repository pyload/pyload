{% autoescape true %}

document.addEvent("domready", function() {
    window.load = new Fx.Tween($("load-indicator"), {
        link: "cancel"
    });
    window.load.set("opacity", 0);
    window.packageBox = new MooDialog({
        destroyOnHide: false
    });
    window.packageBox.setContent($('pack_box'));
    $('pack_reset').addEvent('click', function() {
        $('pack_form').reset();
        window.packageBox.close();
    });
});

function indicateLoad() {
    window.load.start("opacity", 1)
}

function indicateFinish() {
    window.load.start("opacity", 0)
}

function indicateSuccess() {
    indicateFinish();
    window.notify.alert('{{_("Success")}}', {
        'className': 'success'
    });
}

function indicateFail() {
    indicateFinish();
    window.notify.alert('{{_("Failed")}}', {
        'className': 'error'
    });
}
var PackageUI = new Class({
    initialize: function(type) {
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
            var id = ele.getFirst().get("id").match(/[0-9]+/)[0];
            this.packages.push(new Package(this, id, ele))
        }.bind(this))
    },
    loadPackages: function() {},
    deleteFinished: function() {
        indicateLoad();
        new Request.JSON({
            method: 'get',
            url: "{{url_for('api.rpc', func='delete_finished')}}",
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
            url: "{{url_for('api.rpc', func='restart_failed')}}",
            onSuccess: function(data) {
                this.packages.each(function(pack) {
                    pack.close();
                });
                indicateSuccess();
            }.bind(this),
            onFailure: indicateFail
        }).send();
    },
    startSort: function(ele, copy) {},
    saveSort: function(ele, copy) {
        var order = [];
        this.sorts.serialize(function(li, pos) {
            if (li === ele && ele.retrieve("order") !== pos) {
                order.push(ele.retrieve("pid") + '|' + pos)
            }
            li.store("order", pos)
        });
        if (order.length > 0) {
            indicateLoad();
            let pid = order[0].split("|")[0]
            let pos = order[0].split("|")[1]
            new Request.JSON({
                method: 'get',
                url: "{{url_for('json.package_order')}}",
                data: {pid: pid, pos: pos},
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
        this.buttons = new Fx.Tween(this.ele.getElements(".buttons")[0], {
            link: "cancel"
        });
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
            url: "{{url_for('json.package')}}",
            data: {id: + this.id},
            onSuccess: this.createLinks.bind(this),
            onFailure: indicateFail
        }).send();
    },
    createLinks: function(data) {
        var ul = $("sort_children_{id}".substitute({
            id: this.id
        }));
        ul.set("html", "");
        data.links.each(function(link) {
            if (link.status === 0)
                link.icon = 'status-finished.png';
            else if (link.status === 2 || link.status === 3)
                link.icon = 'status-queue.png';
            else if (link.status ===  9 || link.status === 1)
                link.icon = 'status-offline.png';
            else if (link.status === 5)
                link.icon = 'status-waiting.png';
            else if (link.status === 8)
                link.icon = 'status-failed.png';
            else if (link.status === 4)
                link.icon = 'arrow-right';
            else if (link.status ===  11 || link.status === 13)
                link.icon = 'status-proc.png';
            else
                link.icon = 'status-downloading.png';

            link.id = link.fid;
            var li = new Element("li", {
                "style": {
                    "margin-left": 0
                }
            });
            var icon_url = '{{ url_for('static', filename='img/button.png') }}'.replace('button.png', link.icon);
            var html = "<span style='cursor: move' class='child_status sorthandle'><img src='{icon_url}' style='width: 12px; height:12px;'/></span>\n".substitute({
                icon_url: icon_url
            });
            html += "<span style='font-size: 15px'>{name}</span><br /><div class='child_secrow'>".substitute({
                name: link.name
            });
            html += "<span class='child_status'>{statusmsg}</span>{error}&nbsp;".substitute({
                statusmsg: link.statusmsg,
                error: link.error
            });
            html += "<span class='child_status'>{format_size}</span>".substitute({
                format_size: link.format_size
            });
            html += "<span class='child_status'>{plugin}</span>&nbsp;&nbsp;".substitute({
                plugin: link.plugin
            });
            html += "<img title='{{_('Delete Link')}}' style='cursor: pointer;' width='10px' height='10px' src='{{ url_for('static', filename='img/delete.png') }}' />&nbsp;&nbsp;";
            html += "<img title='{{_('Restart Link')}}' style='cursor: pointer;margin-left: -4px' width='10px' height='10px' src='{{ url_for('static', filename='img/arrow-refresh.png') }}' /></div>";
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
            var imgs = child.getElements('.child_secrow img');
            imgs[0].addEvent('click', function(e) {
                new Request({
                    method: 'get',
                    url: "{{url_for('api.rpc', func='delete_files')}}/[" + this + ']',
                    onSuccess: function() {
                        $('file_' + this).nix()
                    }.bind(this),
                    onFailure: indicateFail
                }).send();
            }.bind(lid));
            imgs[1].addEvent('click', function(e) {
                new Request({
                    method: 'get',
                    url: "{{url_for('api.rpc', func='restart_file')}}/" + this,
                    onSuccess: function() {
                        var ele = $('file_' + this);
                        var imgs = ele.getElements("img");
                        imgs[0].set("src", "{{ url_for('static', filename='img/status-queue.png') }}");
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
            url: "{{url_for('api.rpc', func='delete_packages')}}/[" + this.id + ']',
            onSuccess: function() {
                this.ele.nix();
                indicateFinish();
            }.bind(this),
            onFailure: indicateFail
        }).send();
        event.stop();
    },
    restartPackage: function(event) {
        indicateLoad();
        new Request({
            method: 'get',
            url: "{{url_for('api.rpc', func='restart_package')}}/" + this.id,
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
        var ul = $("sort_children_{id}".substitute({
            id: this.id
        }));
        ul.erase("html");
        this.linksLoaded = false;
    },
    movePackage: function(event) {
        indicateLoad();
        new Request({
            method: 'get',
            url: "{{url_for('json.move_package')}}",
            data: {id: this.id, dest: ((this.ui.type + 1) % 2)},
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
        window.packageBox.open();
        event.stop();
    },
    savePackage: function(event) {
        $("pack_form").send();
        this.name.set("text", $("pack_name").get("value"));
        this.folder.set("text", $("pack_folder").get("value"));
        this.password.set("text", $("pack_pws").get("value"));
        window.packageBox.close();
        event.stop();
    },
    saveSort: function(ele, copy) {
        var order = [];
        this.sorts.serialize(function(li, pos) {
            if (li === ele && ele.retrieve("order") !== pos) {
                order.push([ele.retrieve("lid"), pos])
            }
            li.store("order", pos)
        });
        if (order.length > 0) {
            indicateLoad();
            new Request.JSON({
                method: 'get',
                url: "{{url_for('json.link_order')}}",
                data: {fid: order[0][0], pos: order[0][1]},
                onSuccess: indicateFinish,
                onFailure: indicateFail
            }).send();
        }
    }
});

{% endautoescape %}
