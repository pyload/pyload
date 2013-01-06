define(['jquery', 'underscore', 'backbone'],
    function($, _, Backbone) {

        // Renders a single package item
        return Backbone.View.extend({

            el: "#content",
            template_menu: _.compile($("#template-menu").html()),

            events: {
                'click .settings-menu li > a': 'change_section'
            },

            menu: null,
            data: null,

            initialize: function() {
                this.menu = $('.settings-menu');
                var self = this;

//                $.ajax("/api/getCoreConfig", {success: function(data) {
//                    self.data = data;
//                    self.render()
//                }});
//                $.ajax("/api/getPluginConfig");
                console.log("Settings initialized");
            },

            // TODO: this is only a showcase
            render: function() {
                this.menu.html(this.template_menu({core:false}));
            },

            change_section: function(el) {
                console.log("Section changed");
            }

        });
    });