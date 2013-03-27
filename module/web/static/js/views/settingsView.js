define(['jquery', 'underscore', 'backbone', 'app', 'models/ConfigHolder', './configSectionView'],
    function($, _, Backbone, App, ConfigHolder, configSectionView) {

        // Renders settings over view page
        return Backbone.View.extend({

            el: "#content",
            templateMenu: _.compile($("#template-menu").html()),

            events: {
                'click .settings-menu li > a': 'change_section'
            },

            menu: null,
            content: null,

            core_config: null, // It seems models are not needed
            plugin_config: null,

            // currently open configHolder
            config: null,
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
                    self.core_config = data;
                    self.render();
                }}));
                $.ajax(App.apiRequest("getPluginConfig", null, {success: function(data) {
                    self.plugin_config = data;
                    self.render();
                }}));
            },

            render: function() {
                this.menu.html(this.templateMenu({
                    core: this.core_config,
                    plugin: this.plugin_config
                }));
            },

            openConfig: function(name) {
                // Do nothing when this config is already open
                if (this.config && this.config.get('name') === name)
                    return;

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
                // TODO: better cleaning of old views
                var oldHeight = this.content.height();
                this.content.empty();
                this.content.css('display', 'block');
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

            },

            change_section: function(e) {
                // TODO check for changes

                var el = $(e.target).parent();
                var name = el.data("name");
                this.openConfig(name);

                this.menu.find("li.active").removeClass("active");
                el.addClass("active");
                e.preventDefault();
            }

        });
    });