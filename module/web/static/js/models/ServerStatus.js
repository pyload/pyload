define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    return Backbone.Model.extend({

        defaults: {
            queuedDownloads: -1,
            totalDownloads: -1,
            speed: -1,
            pause: false,
            download: false,
            reconnect: false,
        },

        // Model Constructor
        initialize: function() {

        }

    });
});