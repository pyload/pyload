define(['jquery', 'backbone', 'underscore', 'utils/apitypes'], function($, Backbone, _, Api) {

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

        save: function(options){
            // TODO
        }
    });

});