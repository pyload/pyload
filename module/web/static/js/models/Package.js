define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    return Backbone.Model.extend({

        idAttribute: 'pid',

        defaults: {
            pid: -1,
            name : null,
            folder: "",
            root: -1,
            owner: -1,
            site: "",
            comment: "",
            password: "",
            added: -1,
            status: -1,
            packageorder: -1,
            stats: null,
            fids: null,
            pids: null,
            files: null, // Collection
            packs: null // Collection
        },

        // Model Constructor
        initialize: function() {

        },

        // Changes url + method and delegates call to super class
        fetch: function(options) {
            options || (options = {});
            options.url = 'api/getPackageInfo/' + this.get('pid');
            options.type = "post";

            return Backbone.Model.prototype.fetch.call(options);

        },

        save: function(options) {
            // TODO
        },

        // Any time a model attribute is set, this method is called
        validate: function(attrs) {

        }

    });

});