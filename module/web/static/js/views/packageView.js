define(['jquery', 'views/abstract/itemView', 'underscore', 'views/fileView'],
    function($, itemView, _, fileView) {

        // Renders a single package item
        return itemView.extend({

            tagName: 'li',
            className: 'package-view',
            template: _.compile($("#template-package").html()),
            events: {
                'click .package-row .name': 'expand',
                'click .btn-remove': 'delete',
                'click .checkbox': 'select'
            },

            ul: null,

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
                else if (!fileOnly)
                    container.replaceWith(this.template(this.model.toJSON()));

                // TODO: could be done in template
                if (this.model.get('checked'))
                    this.$('.checkbox').addClass('checked');
                else
                    this.$('.checkbox').removeClass('checked');

                // Only create this views a single time
                if (!this.ul && this.model.isLoaded()) {
                    console.log('Rendered content of package ' + this.model.get('pid'));
                    var ul = $('<ul></ul>');
                    ul.addClass('file-items');

                    this.model.get('files').each(function(file) {
                        ul.append(new fileView({model: file}).render().el);
                    });

                    // TODO: additionally it could be placed out of viewport first
                    // The real height can only be retrieved when element is on DOM and display:true
                    ul.css('visibility', 'hidden');
                    this.$el.append(ul);

                    var height = ul.height();

                    // Hide the element when not expanded
                    if (!this.expanded) {
                        ul.hide();
                        ul.height(0);
                    }

                    ul.css('visibility', '');
                    ul.data('height', height);
                    console.log(ul.data("height"));

                    this.ul = ul;
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

            // Toggle expanding of packages
            expand: function(e) {
                e.preventDefault();
                var self = this;

                //  this assumes the ul was created after item was rendered
                if (!this.expanded) {
                    this.model.fetch({silent: true, success: function() {
                        self.render(true);
                        self.ul.animate({height: self.ul.data('height'), opacity: 'show'});
                        self.expanded = true;
                    }});
                } else {
                    this.expanded = false;
                    this.ul.animate({height: 0, opacity: 'hide'});
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