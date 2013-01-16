define(['jquery', 'underscore', 'backbone'],
    function($, _, Backbone) {

        // Renders settings over view page
        return Backbone.View.extend({

            el: "#content",
            template_menu: _.compile($("#template-menu").html()),

            events: {
                'click .settings-menu li > a': 'change_section'
            },

            menu: null,

            core_config: null, // It seems models are not needed
            plugin_config: null,

            initialize: function() {
                this.menu = $('.settings-menu');
                this.refresh();

                console.log("Settings initialized");
            },

            refresh: function() {
                var self = this;
                $.ajax("/api/getCoreConfig", {success: function(data) {
                    self.core_config = data;
                    self.render()
                }});
                $.ajax("/api/getPluginConfig", {success: function(data) {
                    self.plugin_config = data;
                    self.render();
                }});
            },

            render: function() {
                this.menu.html(this.template_menu({
                        core: this.core_config,
                        plugin: this.plugin_config
                    }));
            },

            change_section: function(e) {
                var el = $(e.target).parent();
                var name = el.data("name");
                console.log("Section changed to " + name);

                this.menu.find("li.active").removeClass("active");
                el.addClass("active");
                e.preventDefault();
            }

        });
    });