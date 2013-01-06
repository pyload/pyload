define(['jquery', 'underscore', 'backbone'],
    function($, _, Backbone) {

        // Renders a single package item
        return Backbone.View.extend({

            el: "#content",
//            template: _.compile($("#template-package").html()),

            events: {

            },

            initialize: function() {
                $.ajax("/api/getCoreConfig");
                $.ajax("/api/getPluginConfig");
                $.ajax("/api/getAvailablePlugins");
                console.log("Settings initialized");
            },

            render: function() {
            }

        });
    });