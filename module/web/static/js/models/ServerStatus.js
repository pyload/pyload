define(['jquery', 'backbone', 'underscore', 'collections/ProgressList'],
    function($, Backbone, _, ProgressList) {

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

        },

        fetch: function() {
            options || (options = {});
            options.url = 'api/getServerStatus';

            return Backbone.Model.prototype.fetch.call(this, options);
        },

        parse: function(resp, xhr) {
            // Package is loaded from tree collection
            if (_.has(resp, 'root')) {
                resp.root.files = new FileList(_.values(resp.files));
                // circular dependencies needs to be avoided
                var PackageList = require('collections/PackageList');
                resp.root.packs = new PackageList(_.values(resp.packages));
                return resp.root;
            }
            return Backbone.model.prototype.fetch.call(this, resp, xhr);
        }

    });
});