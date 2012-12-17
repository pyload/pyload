define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    return Backbone.Model.extend({

        idAttribute: 'fid',

        defaults: {
            fid: -1,
            name: null,
            package: -1,
            owner: -1,
            size: -1,
            status: -1,
            media: -1,
            added: -1,
            fileorder: -1,
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