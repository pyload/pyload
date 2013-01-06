define(['jquery', 'underscore', 'backbone'],
    function($, _, Backbone) {

        // Renders a single package item
        return Backbone.View.extend({

            el: "#content",
//            template: _.compile($("#template-package").html()),

            events: {

            },

            menu: null,
            data: null,

            initialize: function() {
                this.menu = $('.settings-menu');
                var self = this;

                $.ajax("/api/getCoreConfig", {success: function(data) {
                    self.data = data;
                    self.render()
                }});
//                $.ajax("/api/getPluginConfig");
                console.log("Settings initialized");
            },

            render: function() {
                if (this.data != null) {
                    var self = this;
                    this.menu.empty();
                    this.menu.append($('<li class="nav-header"><i class="icon-globe icon-white"></i>General</li>'));

                    _.each(this.data, function(section) {
                        self.menu.append($('<li><a href="#">' + section.label + '</a></li>'));
                    })
                }
            }

        });
    });