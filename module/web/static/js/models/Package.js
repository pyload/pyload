define(['jquery', 'backbone', 'underscore', 'collections/FileList', 'require'],
    function($, Backbone, _, FileList, require) {

        return Backbone.Model.extend({

            idAttribute: 'pid',

            defaults: {
                pid: -1,
                name: null,
                folder: "",
                root: -1,
                owner: -1,
                site: "",
                comment: "",
                password: "",
                added: -1,
                tags: null,
                status: -1,
                shared: false,
                packageorder: -1,
                stats: null,
                fids: null,
                pids: null,
                files: null, // Collection
                packs: null, // Collection

                selected: false // For Checkbox
            },

            // Model Constructor
            initialize: function() {
            },

            // Changes url + method and delegates call to super class
            fetch: function(options) {
                options || (options = {});
                options.url = 'api/getFileTree/' + this.get('pid') + '/false';
                options.type = "post";

                return Backbone.Model.prototype.fetch.call(this, options);
            },

            // Create a pseudo package und use search to populate data
            search: function(qry, options) {
                options || (options = {});
                options.url = 'api/findFiles/"' + qry + '"';
                options.type = "post";

                return Backbone.Model.prototype.fetch.call(this, options);
            },

            save: function(options) {
                // TODO
            },

            destroy: function(options) {
                options || (options = {});
                // TODO: as post data
                options.url = 'api/deletePackages/[' + this.get('pid') + ']';
                options.type = "post";

                return Backbone.Model.prototype.destroy.call(this, options);
            },

            restart: function(options) {
                options || (options = {});
                var self = this;
                options.url = 'api/restartPackage/' + this.get('pid');
                options.success = function() {
                    self.fetch();
                };
                return $.ajax(options);
            },

            parse: function(resp) {
                // Package is loaded from tree collection
                if (_.has(resp, 'root')) {
                    if (!this.has('files'))
                        resp.root.files = new FileList(_.values(resp.files));
                    else
                        this.get('files').update(_.values(resp.files));

                    // circular dependencies needs to be avoided
                    var PackageList = require('collections/PackageList');

                    if (!this.has('packs'))
                        resp.root.packs = new PackageList(_.values(resp.packages));
                    else
                        this.get('packs').update(_.values(resp.packages));

                    return resp.root;
                }
                return Backbone.model.prototype.parse.call(this, resp);
            },

            // Any time a model attribute is set, this method is called
            validate: function(attrs) {

            }

        });
    });