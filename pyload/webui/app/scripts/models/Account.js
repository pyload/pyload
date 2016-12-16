define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', './ConfigItem'], function($, Backbone, _, App, Api, ConfigItem) {
    'use strict';

    return Backbone.Model.extend({

        idAttribute: 'aid',

        defaults: {
            aid: null,
            plugin: null,
            loginname: null,
            owner: -1,
            valid: false,
            validuntil: -1,
            trafficleft: -1,
            maxtraffic: -1,
            premium: false,
            activated: false,
            shared: false,
            config: null
        },

        // Model Constructor
        initialize: function() {
        },

        // Any time a model attribute is set, this method is called
        validate: function(attrs) {

        },

        // representation handled by server
        toServerJSON: function() {
            var data = this.toJSON();
            delete data.config;

            return data;
        },

        parse: function(resp) {
            // Convert config to models
            resp.config = _.map(resp.config, function(item) {
                return new ConfigItem(item);
            });

            // JS uses time based on ms
            if (resp.validuntil > 0)
                resp.validuntil *= 1000;

            return resp;
        },

        fetch: function(options) {
            var refresh = _.has(options, 'refresh') && options.refresh;
            options = App.apiRequest('getAccountInfo',
                {plugin: this.get('plugin'),
                    aid: this.get('aid'), refresh: refresh}, options);

            return Backbone.Model.prototype.fetch.call(this, options);
        },

        setPassword: function(password, options) {
            options = App.apiRequest('updateAccount',
                {aid: this.get('aid'),
                    plugin: this.get('plugin'), loginname: this.get('loginname'), password: password}, options);

            return $.ajax(options);
        },

        save: function() {
            // use changed config items only
            var data = this.toJSON();
            data.config = _.map(_.filter(data.config, function(c) {
                return c.isChanged();
            }), function(c) {
                return c.prepareSave();
            });

            // On success wait 1sec and trigger event to reload info
            var options = App.apiRequest('updateAccountInfo', {account: data}, {
                success: function() {
                    _.delay(function() {
                        App.vent.trigger('account:updated');
                    }, 1000);
                }
            });
            return $.ajax(options);
        },

        destroy: function(options) {
            options = App.apiRequest('removeAccount', {account: this.toServerJSON()}, options);
            var self = this;
            options.success = function() {
                self.trigger('destroy', self, self.collection, options);
            };

            // TODO request is not dispatched
//            return Backbone.Model.prototype.destroy.call(this, options);
            return $.ajax(options);
        }
    });

});
