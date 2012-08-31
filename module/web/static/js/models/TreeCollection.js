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

        parse: function(resp, xhr) {
            return {
              root: new Package(resp.root),
              packages: new PackageList(_.values(resp.packages)),
              files: new FileList(_.values(resp.files))
            };
        }

    });
});