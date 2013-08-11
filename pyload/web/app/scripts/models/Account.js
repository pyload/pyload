define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'], function($, Backbone, _, App, Api) {
    'use strict';

    return Backbone.Model.extend({

        // TODO
        // generated, not submitted
        idAttribute: 'loginname',

        defaults: {
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

        fetch: function(options) {
            var refresh = _.has(options, 'refresh') && options.refresh;
            options = App.apiRequest('getAccountInfo',
                {plugin: this.get('plugin'),
                    loginname: this.get('loginname'), refresh: refresh}, options);

            return Backbone.Model.prototype.fetch.call(this, options);
        },

        setPassword: function(password, options) {
            options = App.apiRequest('updateAccount',
                {plugin: this.get('plugin'), loginname: this.get('loginname'), password: password}, options);

            return $.ajax(options);
        },

        save: function() {
            // On success wait 1sec and trigger event to reload info
            var options = App.apiRequest('updateAccountInfo', {account: this.toJSON()}, {
                success: function() {
                    _.delay(function() {
                        App.vent.trigger('accounts:updated');
                    }, 1000);
                }
            });
            return $.ajax(options);
        },

        destroy: function(options) {
            options = App.apiRequest('removeAccount', {account: this.toJSON()}, options);
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