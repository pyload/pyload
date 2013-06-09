define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'], function($, Backbone, _, App, Api) {
    'use strict';

    return Backbone.Model.extend({

        // TODO
        // generated, not submitted
        idAttribute: 'user',

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
            options: null
        },

        // Model Constructor
        initialize: function() {
        },

        // Any time a model attribute is set, this method is called
        validate: function(attrs) {

        },

        save: function(options) {
            options = App.apiRequest('updateAccountInfo', {account: this.toJSON()}, options);
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