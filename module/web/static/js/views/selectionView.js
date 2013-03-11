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

            // Element of the action bar
            actionBar: null,
            // number of currently selected elements
            current: 0,

            initialize: function() {
                this.$el.calculateHeight().height(0);

                var render = _.bind(this.render, this);

                App.vent.on('dashboard:updated', render);
                App.vent.on('dashboard:filtered', render);
                App.vent.on('package:selection', render);
                App.vent.on('file:selection', render);

                this.actionBar = $('.actionbar .btn-check');
                this.actionBar.parent().click(_.bind(this.select_toggle, this));
                // TODO when something gets deleted
//                this.tree.get('packages').on('delete', _.bind(this.render, this));
            },

            get_files: function(all) {
                var files = [];
                if (App.dashboard.files)
                    if (all)
                        files = App.dashboard.files.where({visible: true});
                    else
                        files = App.dashboard.files.where({selected: true, visible: true});

                return files;
            },

            get_packs: function() {
                return App.dashboard.tree.get('packages').where({selected: true});
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

            // Deselects all items
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
                _.confirm('default/confirmDialog.html', function() {
                    alert("Not implemented yet");
                    this.deselect();
                }, this);
            },

            trash: function() {
                // TODO: delete many at once, check if package is parent
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
                    this.get_files(true).map(function(file) {
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