define(['jquery', 'backbone', 'underscore'],
    function($, Backbone, _) {

    return Backbone.Model.extend({

        defaults: {
            speed: 0,
            files: null,
            notifications: -1,
            paused: false,
            download: false,
            reconnect: false
        },

        // Model Constructor
        initialize: function() {

        },

        fetch: function() {
            options || (options = {});
            options.url = 'api/getServerStatus';

            return Backbone.Model.prototype.fetch.call(this, options);
        },

        toJSON: function(options) {
            var obj = Backbone.Model.prototype.toJSON.call(this, options);

            // stats are not available
            if (obj.files === null)
                return obj;

            obj.files.linksleft = obj.files.linkstotal - obj.files.linksdone;
            obj.files.sizeleft = obj.files.sizetotal - obj.files.sizedone;
            if (obj.speed && obj.speed > 0)
                obj.files.eta = Math.round(obj.files.sizeleft / obj.speed);
            else if (obj.files.sizeleft > 0)
                obj.files.eta = Infinity;
            else
                obj.files.eta = 0;

            return obj;
        }

    });
});