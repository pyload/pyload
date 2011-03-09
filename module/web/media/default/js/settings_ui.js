var account_dialog;

function show_account_dialog() {
    bg_show();
    $("account_box").setStyle('display', 'block');
    account_dialog.start('opacity', 1)
}

function hide_account_dialog() {
    bg_hide();
    account_dialog.start('opacity', 0).chain(function() {
        $('account_box').setStyle('display', 'none');
    });
}


var SettingsUI = new Class({
            initialize: function() {
                this.menu = $$("#general-menu li");
                this.menu.append($$("#plugin-menu li"));

                this.name = $("tabsback");
                this.general = $("general_form_content");
                this.plugin = $("plugin_form_content");

                this.menu.each(function(el) {
                    el.addEvent("click", this.menuClick.bind(this));
                }.bind(this));


                $("general|submit").addEvent("click", this.configSubmit.bind(this));
                $("plugin|submit").addEvent("click", this.configSubmit.bind(this));

                $("account_add").addEvent("click", function(e) {
                    show_account_dialog();
                    e.stop();
                });

                $("account_reset").addEvent("click", function(e) {
                    hide_account_dialog();
                });

                $("account_add_button").addEvent("click", this.addAccount.bind(this));
                $("account_submit").addEvent("click", this.submitAccounts.bind(this));


            },

            menuClick: function(e) {
                var string = e.target.get("id").split("|");
                var category = string[0];
                var section = string[1];
                var name = e.target.get("text");

                if (category == "general") {
                    var target = this.general;
                } else if (category == "plugin") {
                    var target = this.plugin;
                }

                target.dissolve();

                new Request({
                            "method" : "get",
                            "url" : "/json/load_config/" + category + "/" + section,
                            "onSuccess": function(data) {
                                target.set("html", data);
                                target.reveal();
                                this.name.set("text", name);
                            }.bind(this)
                        }).send();
            },

            configSubmit: function(e) {
                var string = e.target.get("id").split("|");
                var category = string[0];

                var form = $(category + "_form");


                form.set("send", {
                            "method": "post",
                            "url": "/json/save_config/" + category,
                            "onSuccess" : function() {
                                notify.alert('Settings saved', {
                                            'className': 'success'
                                        });

                            },
                            "onFailure": function() {
                                notify.alert('Error occured', {
                                            'className': 'error'
                                        });
                            }
                        });

                form.send();

                e.stop();

            },
            addAccount: function(e) {

                var form = $("add_account_form");
                form.set("send", {
                            "method": "post",
                            "onSuccess" : function() {
                                window.location.reload()
                            },
                            "onFailure": function() {
                                notify.alert('Error occured', {
                                            'className': 'error'
                                        });
                            }
                        });

                form.send();


                e.stop();
            },

            submitAccounts: function(e) {

                var form = $("account_form");
                form.set("send", {
                            "method": "post",
                            "onSuccess" : function() {
                                window.location.reload()
                            },
                            "onFailure": function() {
                                notify.alert('Error occured', {
                                            'className': 'error'
                                        });
                            }
                        });

                form.send();


                e.stop();

                e.stop();
            }
        });
