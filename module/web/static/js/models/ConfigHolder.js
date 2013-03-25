define(['jquery', 'backbone', 'underscore', 'app', './ConfigItem'],
    function($, Backbone, _, App, ConfigItem) {

        return Backbone.Model.extend({

            defaults: {
                name: "",
                label: "",
                description: "",
                long_description: null,
                // simple list but no collection
                items: null,
                info: null
            },

            // Model Constructor
            initialize: function() {

            },

            // Loads it from server by name
            fetch: function(options) {
                options = App.apiRequest('loadConfig/"' + this.get('name') + '"', null, options);
                return Backbone.Model.prototype.fetch.call(this, options);
            },

            save: function(options) {
                // TODO
            },

            parse: function(resp) {
                // Create item models
                resp.items = _.map(resp.items, function(item) {
                    return new ConfigItem(item);
                });

                return Backbone.Model.prototype.parse.call(this, resp);
            },

            isLoaded: function() {
                return this.has('items') || this.has('long_description');
            }
        });
    });