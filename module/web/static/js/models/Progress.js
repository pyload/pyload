define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    return Backbone.Model.extend({

        // generated, not submitted
        idAttribute: 'pid',

        defaults: {
            pid: -1,
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

        toJSON: function(options) {
            var obj = Backbone.Model.prototype.toJSON.call(this, options);
            if (obj.total > 0)
                obj.percent = Math.round(obj.done * 100 / obj.total);
            else
                obj.percent = 0;

            return obj;
        },

        isDownload : function() {
            return this.has('download');
        }

    });

});