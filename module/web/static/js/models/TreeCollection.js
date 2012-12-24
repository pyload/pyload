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

            console.log('Fetching package tree ' + pid);

            return Backbone.Model.prototype.fetch.call(this, options);
        },

        // Parse the response and updates the collections
        parse: function(resp) {
            var ret = {};
            if (!this.has('packages'))
                ret.packages = new PackageList(_.values(resp.packages));
            else
                this.get('packages').update(_.values(resp.packages));

            if (!this.has('files'))
                ret.files = new FileList(_.values(resp.files));
            else
                this.get('files').update(_.values(resp.files));

            ret.root = new Package(resp.root);
            return ret;
        }

    });
});