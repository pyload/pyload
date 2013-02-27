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
            // Element of the action bar
            actionBar: null,
            // needed to know when slide down
            current: 0,

            initialize: function(tree) {
                this.tree = tree;
                this.files = tree.get('files');

                App.vent.on('dashboard:show', _.bind(this.set_files, this));
                App.vent.on('package:selection', _.bind(this.render, this));
                App.vent.on('file:selection', _.bind(this.render, this));

                this.actionBar = $('.actionbar .btn-check');
                this.actionBar.parent().click(_.bind(this.select_toggle, this));

                // TODO when something gets deleted
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

                if (files > 0)
                    this.actionBar.addClass('iconf-check').removeClass('iconf-check-empty');
                else
                    this.actionBar.addClass('iconf-check-empty').removeClass('iconf-check');

                this.current = files + packs;
            },

            set_files: function(files) {
                this.files = files;
                this.render();
            },

            // Deselects all items, optional only files
            deselect: function(filesOnly) {
                this.get_files().map(function(file) {
                    file.set('selected', false);
                });

                this.get_packs().map(function(pack) {
                    pack.set('selected', false);
                });

                this.render();
            },

            pause: function() {
                _.confirm('default/confirmDialog.html', function() {
                    alert("Not implemented yet");
                    this.deselect();
                }, this);
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
            },

            // Select or deselect all visible files
            select_toggle: function() {
                var files = this.get_files();
                if (files.length === 0) {
                    // TODO Select only visible files
                    this.files.map(function(file) {
                        file.set('selected', true);
                    });

                } else
                    files.map(function(file) {
                        file.set('selected', false);
                    });

                this.render();
            }
        });
    });