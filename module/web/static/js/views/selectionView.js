define(['jquery', 'backbone', 'underscore', 'app'],
    function($, Backbone, _, App) {

        // Renders context actions for selection packages and files
        return Backbone.View.extend({
            el: '#selection-area',
            template: _.compile($("#template-select").html()),

            events: {
                'click .iconf-check': 'deselect',
                'click .iconf-pause': 'pause',
                'click .iconf-trash': 'trash',
                'click .iconf-refresh': 'restart'
            },

            // available packages
            tree: null,
            // selected files
            files: null,
            // needed to know when slide down
            current: 0,

            initialize: function(tree) {
                this.tree = tree;
                this.files = tree.get('files');

                App.vent.on('dashboard:show', _.bind(this.set_files, this));
                App.vent.on('package:selection', _.bind(this.render, this));
                App.vent.on('file:selection', _.bind(this.render, this));

                // TODO
//                this.tree.get('packages').on('delete', _.bind(this.render, this));
            },

            get_files: function() {
                var files = [];
                if (this.files)
                    files = this.files.where({selected: true});

                return files;
            },

            get_packs: function() {
                return this.tree.get('packages').where({selected: true});
            },

            render: function() {
                var files = this.get_files().length;
                var packs = this.get_packs().length;

                if (files + packs > 0) {
                    this.$el.html(this.template({files: files, packs: packs}));
                    this.$el.initTooltips('bottom');
                }

                if (files + packs > 0 && this.current === 0)
                    this.$el.slideOut();
                else if (files + packs === 0 && this.current > 0)
                    this.$el.slideIn();

                this.current = files + packs;

            },

            set_files: function(files) {
                this.files = files;
                this.render();
            },

            deselect: function() {
                this.get_files().map(function(file) {
                    file.set('selected', false);
                });

                this.get_packs().map(function(pack) {
                    pack.set('selected', false);
                });

                this.render();
            },

            pause: function() {
                // TODO
            },

            trash: function() {
                this.get_files().map(function(file) {
                    file.destroy();
                });

                this.get_packs().map(function(pack) {
                    pack.destroy();
                });

                this.deselect();
            },

            restart: function() {
                this.get_files().map(function(file) {
                    file.restart();
                });
                this.get_packs().map(function(pack) {
                    pack.restart();
                });

                this.deselect();
            }
        });
    });