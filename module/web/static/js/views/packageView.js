define(['jquery', 'views/abstract/itemView', 'underscore', 'views/fileView'],
    function($, itemView, _, fileView) {

        // Renders a single package item
        return itemView.extend({

            tagName: 'li',
            className: 'package-view',
            template: _.compile($("#template-package").html()),
            events: {
                'click .package-row .name': 'expand',
                'click .delete': 'delete',
                'click .checkbox': 'select'
            },

            // File views visible
            expanded: false,

            initialize: function() {
                this.model.on('filter:added', this.hide, this);
                this.model.on('filter:removed', this.show, this);
                this.model.on('change', this.render, this);
                this.model.on('remove', this.unrender, this);
            },

            onDestroy: function() {
                this.model.off('filter:added', this.hide); // TODO
            },

            // Render everything, optional only the fileViews
            render: function(fileOnly) {
                var container = this.$('.package-header');
                if (!container.length)
                    this.$el.html(this.template(this.model.toJSON()));
                else if(!fileOnly)
                    container.replaceWith(this.template(this.model.toJSON()));

                // TODO: could be done in template
                if (this.model.get('checked'))
                    this.$('.checkbox').addClass('checked');
                else
                    this.$('.checkbox').removeClass('checked');

                // Only create this views a single time
                var ul = this.$('ul');
                if (!ul.length && this.model.isLoaded()) {
                    console.log('Rendered content of package ' + this.model.get('pid'));
                    ul = $('<ul></ul>');

                    if(!this.expanded)
                        ul.hide();

                    this.model.get('files').each(function(file) {
                        ul.append(new fileView({model: file}).render().el);
                    });
                    this.$el.append(ul);
                }
                return this;
            },

            unrender: function() {
                var self = this;
                this.$el.zapOut(function() {
                    self.destroy();
                });

                // TODO destroy the fileViews ?
            },

            // TODO: animation
            // Toggle expanding of packages
            expand: function(e) {
                e.preventDefault();
                var self = this;

                if (!this.expanded) {
                    this.model.fetch({silent: true, success: function() {
                        self.render(true);
                        self.$('ul').show();
                        self.expanded = true;
                    }});
                } else {
                    this.expanded = false;
                    this.$('ul').hide();
                }
            },

            select: function(e) {
                e.preventDefault();
                var checked = this.$('.checkbox').hasClass('checked');
                // toggle class immediately, so no re-render needed
                this.model.set('checked', !checked, {silent: true});
                this.$('.checkbox').toggleClass('checked');
            }

        });
    });