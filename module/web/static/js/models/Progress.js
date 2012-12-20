define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    return Backbone.Model.extend({

// TODO
//        idAttribute: 'fid',

        defaults: {
            plugin: null,
            name: null,
            statusmsg: -1,
            eta: -1,
            done: -1,
            total: -1,
            download: null
        },


        // Model Constructor
        initialize: function() {

        },

        // Any time a model attribute is set, this method is called
        validate: function(attrs) {

        },

        isDownload : function() {
            return this.has('download')
        }

    });

});