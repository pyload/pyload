define(['jquery', 'backbone', 'underscore', 'app', 'models/TreeCollection',
    'views/packageView', 'views/fileView', 'views/selectionView'],
    function($, Backbone, _, App, TreeCollection, packageView, fileView, selectionView) {

        // Renders whole PackageView
        return Backbone.View.extend({

            el: '#content',

            events: {
                'click #show_active': 'filter'
            },

            // <ul> holding the packages
            packageUL: null,
            // <ul> displaying the files
            fileUL: null,
            // current open model
            opened: null,
            // Current open files
            files: null,

            initialize: function() {
                var self = this;
                this.tree = new TreeCollection();

                var view = new selectionView(this.tree);

                // When package is added we reload the data
                App.vent.on('package:added', function() {
                    console.log('Package tree caught, package:added event');
                    self.tree.fetch();
                });

                App.vent.on('dashboard:loading', _.bind(this.loading, this));
                App.vent.on('dashboard:show', _.bind(this.show, this));
            },

            init: function() {
                var self = this;

                // TODO: put in separated function
                // TODO: order of elements?
                // Init the tree and callback for package added
                this.tree.fetch({success: function() {
                    self.render();
                    self.tree.get('packages').on('add', function(pack) {
                        console.log('Package ' + pack.get('pid') + ' added to tree');
                        self.appendPackage(pack, 0, true);

                    });
                }});
            },

            render: function() {
                var packs = this.tree.get('packages');
                this.files = this.tree.get('files');

                this.packageUL = this.$('.package-list');
                packs.each(_.bind(this.appendPackage, this));

                this.fileUL = this.$('.file-list');
                this.files.each(_.bind(this.appendFile, this));

                return this;
            },

            // TODO sorting ?!
            // Append a package to the list, index, animate it
            appendPackage: function(pack, i, animation) {
                var el = new packageView({model: pack}).render().el;
                this.packageUL.appendWithAnimation(el, animation);
            },

            appendFile: function(file, i, animation) {
                var el = new fileView({model: file}).render().el;
                this.fileUL.appendWithAnimation(el, animation);
            },

            loading: function(model) {
                // nothing to load when it is already open
//                if (this.opened === model)
//                    return;
                // TODO: do not rerender already opened
                this.opened = model;
                this.files = null;
//                this.fileUL.fadeOut();
                this.fileUL.empty();
            },

            failure: function() {
                // TODO
            },

            show: function(files) {
                this.files = files;
                files.each(_.bind(this.appendFile, this));
                this.fileUL.fadeIn();
            },

            // TODO: remove this debug stuff
            toggle: false,
            filter: function(e) {
                var self = this;
                this.tree.get('packages').each(function(item) {
                    if (!self.toggle)
                        item.trigger('filter:added');
                    else
                        item.trigger('filter:removed');

                });
                self.toggle ^= true;
            }
        });
    });