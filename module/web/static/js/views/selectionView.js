define(['jquery', 'backbone', 'underscore', 'app'],
    function($, Backbone, _, App) {

        // Renders context actions for selection packages and files
        return Backbone.View.extend({
            el: '#selection-area',
            template: _.compile($("#template-select").html()),

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
            },

            render: function() {
                var files = 0;
                if (this.files)
                    files = this.files.where({selected: true}).length;

                var packs = this.tree.get('packages').where({selected: true}).length;

                if (files + packs > 0)
                    this.$el.html(this.template({files: files, packs: packs}));

                if (files + packs > 0 && this.current === 0)
                    this.$el.slideOut();
                else if (files + packs === 0 && this.current > 0)
                    this.$el.slideIn();

                this.current = files + packs;

            },

            set_files: function(files) {
                this.files = files;
                this.render();
            }
        });
    });