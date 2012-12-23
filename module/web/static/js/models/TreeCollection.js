define(['jquery', 'backbone', 'underscore', 'models/Package', 'collections/FileList', 'collections/PackageList'],
    function($, Backbone, _, Package, FileList, PackageList) {

    // TreeCollection
    // A Model and not a collection, aggregates other collections
    return Backbone.Model.extend({

        defaults : {
            root: null,
            packages: null,
            files: null
        },

        initialize: function() {

        },

        fetch: function(options) {
            options || (options = {});
            var pid = options.pid || -1;

            // TODO: more options possible
            options.url = 'api/getFileTree/' + pid + '/false';
            options.type = "post";

            return Backbone.Model.prototype.fetch.call(this, options);
        },

        // Parse the response and updates the collections
        parse: function(resp, xhr) {
            if (this.get('packages') === null)
                this.set('packages', new PackageList(_.values(resp.packages)));
            else
                this.packages.update(_.values(resp.packages));

            if (this.get('files') === null)
                this.set('files', new FileList(_.values(resp.files)));
            else
                this.files.update(_.values(resp.files));

            return {
              root: new Package(resp.root)
            };
        }

    });
});