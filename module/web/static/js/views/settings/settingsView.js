define(['jquery', 'underscore', 'backbone', 'app', 'models/ConfigHolder', './configSectionView'],
    function($, _, Backbone, App, ConfigHolder, configSectionView) {

        // Renders settings over view page
        return Backbone.View.extend({

            el: "body",
            templateMenu: _.compile($("#template-menu").html()),

            events: {
                'click .settings-menu li > a': 'change_section',
                'click .btn-add': 'choosePlugin',
                'click .iconf-remove': 'deleteConfig'
            },

            menu: null,
            content: null,
            modal: null,

            coreConfig: null, // It seems collections are not needed
            pluginConfig: null,

            // currently open configHolder
            config: null,
            lastConfig: null,
            isLoading: false,


            initialize: function() {
                this.menu = this.$('.settings-menu');
                this.content = this.$('.setting-box > form');
                // set a height with css so animations will work
                this.content.height(this.content.height());
                this.refresh();

                console.log("Settings initialized");
            },

            refresh: function() {
                var self = this;
                $.ajax(App.apiRequest("getCoreConfig", null, {success: function(data) {
                    self.coreConfig = data;
                    self.render();
                }}));
                $.ajax(App.apiRequest("getPluginConfig", null, {success: function(data) {
                    self.pluginConfig = data;
                    self.render();
                }}));
            },

            render: function() {
                this.menu.html(this.templateMenu({
                    core: this.coreConfig,
                    plugin: this.pluginConfig
                }));
            },

            openConfig: function(name) {
                // Do nothing when this config is already open
                if (this.config && this.config.get('name') === name)
                    return;

                this.lastConfig = this.config;
                this.config = new ConfigHolder({name: name});
                this.loading();

                var self = this;
                this.config.fetch({success: function() {
                    if (!self.isLoading)
                        self.show();

                }, failure: _.bind(this.failure, this)});

            },

            loading: function() {
                this.isLoading = true;
                var self = this;
                this.content.fadeOut({complete: function() {
                    if (self.config.isLoaded())
                        self.show();

                    self.isLoading = false;
                }});

            },

            show: function() {
                // TODO animations are bit sloppy
                this.content.css('display', 'block');
                var oldHeight = this.content.height();

                // this will destroy the old view
                if (this.lastConfig)
                    this.lastConfig.trigger('destroy');
                else
                    this.content.empty();

                // reset the height
                this.content.css('height', '');
                // append the new element
                this.content.append(new configSectionView({model: this.config}).render().el);
                // get the new height
                var height = this.content.height();
                // set the old height again
                this.content.height(oldHeight);
                this.content.animate({
                    opacity: 'show',
                    height: height
                });
            },

            failure: function() {
                // TODO
                this.config =  null;
            },

            change_section: function(e) {
                // TODO check for changes
                // TODO move this into render?

                var el = $(e.target).parent();
                var name = el.data("name");
                this.openConfig(name);

                this.menu.find("li.active").removeClass("active");
                el.addClass("active");
                e.preventDefault();
            },

            choosePlugin: function(e){
                var self = this;
                _.requireOnce(['views/settings/pluginChooserModal'], function(Modal) {
                    if (self.modal === null)
                        self.modal = new Modal();

                    self.modal.show();
                });
            },

            deleteConfig: function(e){
                e.stopPropagation();
                var el = $(e.target).parent().parent();
                var name = el.data("name");

                console.log("Delete config " + name);
            }

        });
    });