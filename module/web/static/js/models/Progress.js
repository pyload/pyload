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

        getPercent: function() {
            if (this.get('total') > 0)
                return Math.round(this.get('done') * 100 / this.get('total'));
            return  0;
        },

        // Model Constructor
        initialize: function() {

        },

        // Any time a model attribute is set, this method is called
        validate: function(attrs) {

        },

        toJSON: function(options) {
            var obj = Backbone.Model.prototype.toJSON.call(this, options);
            obj.percent = this.getPercent();

            return obj;
        },

        isDownload : function() {
            return this.has('download');
        }

    });

});