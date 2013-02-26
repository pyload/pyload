define(['jquery', 'backbone', 'underscore', 'app', 'models/TreeCollection',
    'views/packageView', 'views/fileView', 'views/selectionView', 'views/actionbarView'],
    function($, Backbone, _, App, TreeCollection, packageView, fileView, selectionView, actionbarView) {

        // Renders whole dashboard
        return Backbone.View.extend({

            el: '#content',

            events: {
            },

            // <ul> holding the packages
            packageUL: null,
            // <ul> displaying the files
            fileUL: null,
            // Current open files
            files: null,
            // True when loading animation is running
            isLoading: false,

            initialize: function() {
                var self = this;
                this.tree = new TreeCollection();

                var view = new selectionView(this.tree);
                view = new actionbarView();

                // When package is added we reload the data
                App.vent.on('package:added', function() {
                    console.log('Package tree caught, package:added event');
                    self.tree.fetch();
                });

                // TODO file:added

                App.vent.on('dashboard:loading', _.bind(this.loading, this));
                App.vent.on('dashboard:contentReady', _.bind(this.contentReady, this));
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
                console.log('Render package list');
                var packs = this.tree.get('packages');
                this.files = this.tree.get('files');

                this.packageUL = this.$('.package-list');
                packs.each(_.bind(this.appendPackage, this));

                this.fileUL = this.$('.file-list');
                if (this.files.length === 0)
                    this.fileUL.append($('<li>No package selected</li>'));
                else
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

            contentReady: function(files) {
                // show the files when no loading animation is running and not already open
                if (!this.isLoading && this.files !== files) {
                    this.files = files;
                    this.show();
                } else
                    this.files = files;
            },

            // TODO: better state control of dashboard
            // TODO: elaborate events and reaction
            loading: function(model) {
                // nothing to load when it is already open, or nothing is shown
                if (!this.files || (model && this.files === model.get('files')))
                    return;

                this.isLoading = true;
                this.files = null;
                var self = this;
                // Render when the files are already set
                this.fileUL.fadeOut({complete: function() {
                    if (self.files)
                        self.show();

                    self.isLoading = false;
                }});
            },

            failure: function() {
                // TODO
            },

            show: function() {
                this.fileUL.empty();
                this.files.each(_.bind(this.appendFile, this));
                this.fileUL.fadeIn();
                App.vent.trigger('dashboard:show', this.files);
            }
        });
    });