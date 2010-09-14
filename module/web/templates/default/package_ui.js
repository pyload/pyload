//{% load i18n %}
var load, pack_box;

document.addEvent("domready", function(){
    load = new Fx.Tween($("load-indicator"), {link: "cancel"});
    pack_box = new Fx.Tween($('pack_box'));
    $('pack_reset').addEvent('click', function(){
        hide_pack()
    });
});

function indicateLoad() {
    //$("load-indicator").reveal();
    load.start("opacity", 1)
}

function indicateFinish() {
    load.start("opacity", 0)
}

function show_pack(){
    bg_show();
    $("pack_box").setStyle('display', 'block');
    pack_box.start('opacity',1)
}

function hide_pack(){
    bg_hide();
    pack_box.start('opacity',0).chain(function(){
        $('pack_box').setStyle('display', 'none');
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
            onStart: this.startSort,
            onComplete: this.saveSort.bind(this)
        });
    },

    parsePackages: function() {
        $("package-list").getChildren("li").each(function(ele) {
            var id = ele.getFirst().get("id").match(/[0-9]+/);
            this.packages.push(new Package(this, id, ele))
        }.bind(this))
    },

    loadPackages: function() {

    },

    startSort: function(ele, copy) {
    },

    saveSort: function(ele, copy) {
        var order = [];
        this.sorts.serialize(function(ele,pos){
            if (ele.retrieve("order") != pos){
                order.push(ele.retrieve("pid")+"|"+pos);
                ele.store("order", pos);
            }

        });
        if (order.length > 0){
            indicateLoad();
            new Request.JSON({
                method: 'get',
                url: '/json/package_order/' + order[0],
                onSuccess: indicateFinish,
                onFailure: indicateFinish
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

        pname.addEvent("mouseenter", function(e){
            this.buttons.start("opacity", 1)
        }.bind(this));

        pname.addEvent("mouseleave", function(e){
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
        this.prio = this.ele.getElements('.prio')[0];

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
            onFailure: indicateFinish
        }).send();
    },

    createLinks: function(data) {
        var ul = $("sort_children_{id}".substitute({"id": this.id}));
        ul.erase("html");
        data.links.each(function(link){
            var li = new Element("li",{
                "style": {
                    "margin-left": 0
                }
            });

            var html = "<span style='cursor: move' class='child_status sorthandle'><img src='/media/default/img/{icon}' style='width: 12px; height:12px;'/></span>\n".substitute({"icon": link.icon});
            html += "<span style='font-size: 15px'>{name}</span><br /><div class='child_secrow'>".substitute({"name": link.name});
            html += "<span class='child_status'>{statusmsg}</span>{error}&nbsp;".substitute({"statusmsg": link.statusmsg, "error":link.error});
            html += "<span class='child_status'>{format_size}</span>".substitute({"format_size": link.format_size});
            html += "<span class='child_status'>{plugin}</span>&nbsp;&nbsp;".substitute({"plugin": link.plugin});
            html += "<img title='{% trans "Delete Link" %}' style='cursor: pointer;' width='10px' height='10px' src='{{ MEDIA_URL }}img/delete.png' />&nbsp;&nbsp;";
            html += "<img title='{% trans "Restart Link" %}' style='cursor: pointer;margin-left: -4px' width='10px' height='10px' src='{{ MEDIA_URL }}img/arrow_refresh.png' /></div>";

            var div = new Element("div",{
                "id": "file_"+link.id,
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
        this.ele.getElements('.child').each(function(child){
            var lid = child.get('id').match(/[0-9]+/);
            var imgs = child.getElements('.child_secrow img');
            imgs[0].addEvent('click', function(e){
                new Request({
                    method: 'get',
                    url: '/json/remove_link/'+this,
                    onSuccess: function(){
                        $('file_'+this).nix()
                    }.bind(this)
                }).send();
            }.bind(lid));

            imgs[1].addEvent('click', function(e){
                new Request({
                    method: 'get',
                    url: '/json/restart_link/'+this,
                    onSuccess: function(){
                        $('file_'+this).nix()
                    }.bind(this)
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
            url: '/json/remove_package/'+this.id,
            onSuccess: function(){
                this.ele.nix();
                indicateFinish();
            }.bind(this)
        }).send();
        event.stop();
    },

    restartPackage: function(event) {
        indicateLoad();
        new Request({
            method: 'get',
            url: '/json/restart_package/'+this.id,
            onSuccess: function(){
                var child = this.ele.getElement('.children');
                if (child.getStyle('display') == "block") {
                    child.dissolve();
                }
                var ul = $("sort_children_{id}".substitute({"id": this.id}));
                ul.erase("html");
                this.linksLoaded = false;
                    
                indicateFinish();
            }.bind(this)
        }).send();
        event.stop();
    },

    movePackage: function(event){
        indicateLoad();
        new Request({
            method: 'get',
            url: '/json/move_package/'+((this.ui.type +1) % 2) +"/"+ this.id,
            onSuccess: function(){
                this.ele.nix();
                indicateFinish();
            }.bind(this)
        }).send();
        event.stop();
    },


    editPackage: function(event){
        $("pack_form").removeEvents("submit");
        $("pack_form").addEvent("submit", this.savePackage.bind(this));

        $("pack_id").set("value", this.id);
        $("pack_name").set("value", this.name.get("text"));
        $("pack_folder").set("value", this.folder.get("text"));
        $("pack_pws").set("value", this.password.get("text"));

        var prio = 3;
        $("pack_prio").getChildren("option").each(function(item, index){
           item.erase("selected");
            if (prio.toString() == this.prio.get("text")){
                item.set("selected","selected");
            }
            prio--;
        }.bind(this));


        show_pack();
        event.stop();
    },

    savePackage: function(event){
        $("pack_form").send();
        this.name.set("text", $("pack_name").get("value"));
        this.folder.set("text", $("pack_folder").get("value"));
        this.password.set("text", $("pack_pws").get("value"));
        this.prio.set("text", $("pack_prio").get("value"));
        hide_pack();
        event.stop();
    },

    saveSort: function(ele, copy) {
        var order = [];
        this.sorts.serialize(function(ele,pos){
            if (ele.retrieve("order") != pos){
                order.push(ele.retrieve("lid")+"|"+pos);
                ele.store("order", pos);
            }

        });
        if (order.length > 0){
            indicateLoad();
            new Request.JSON({
                method: 'get',
                url: '/json/link_order/' + order[0],
                onSuccess: indicateFinish,
                onFailure: indicateFinish
            }).send();
        }
    }

});