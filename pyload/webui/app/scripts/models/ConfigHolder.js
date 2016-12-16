define(['jquery', 'backbone', 'underscore', 'app', './ConfigItem'],
    function($, Backbone, _, App, ConfigItem) {
        'use strict';

        return Backbone.Model.extend({

            defaults: {
                name: '',
                label: '',
                description: '',
                explanation: null,
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
                var config = this.toJSON();
                var items = [];
                // Convert changed items to json
                _.each(config.items, function(item) {
                    if (item.isChanged()) {
                        items.push(item.prepareSave());
                    }
                });
                config.items = items;
                // TODO: only set new values on success

                options = App.apiRequest('saveConfig', {config: config}, options);

                return $.ajax(options);
            },

            parse: function(resp) {
                // Create item models
                resp.items = _.map(resp.items, function(item) {
                    return new ConfigItem(item);
                });

                return Backbone.Model.prototype.parse.call(this, resp);
            },

            isLoaded: function() {
                return this.has('items') || this.has('explanation');
            },

            // check if any of the items has changes
            hasChanges: function() {
                var items = this.get('items');
                if (!items) return false;
                return _.reduce(items, function(a, b) {
                    return a || b.isChanged();
                }, false);
            }

        });
    });
