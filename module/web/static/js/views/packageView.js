define(['jquery', 'app', 'views/abstract/itemView', 'underscore'],
    function($, App, itemView, _) {

        // Renders a single package item
        return itemView.extend({

            tagName: 'li',
            className: 'package-view',
            template: _.compile($("#template-package").html()),
            events: {
                'click .package-name': 'open',
                'click .iconf-trash': 'delete',
                'click .select': 'select'
            },

            // Ul for child packages (unused)
            ul: null,
            // Currently unused
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
            render: function() {
                this.$el.html(this.template(this.model.toJSON()));

                return this;
            },

            unrender: function() {
                var self = this;
                this.$el.zapOut(function() {
                    self.destroy();
                });

                // TODO: display other package
            },


            // TODO
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

            open: function(e) {
                var self = this;
                App.vent.trigger('dashboard:loading', this.model);
                this.model.fetch({silent: true, success: function() {
                    console.log('Package ' + self.model.get('pid') + ' loaded');
                    App.vent.trigger('dashboard:show', self.model.get('files'));
                }});
            },

            select: function(e) {
                e.preventDefault();
                var checked = this.$('.select').hasClass('iconf-check');
                // toggle class immediately, so no re-render needed
                this.model.set('selected', !checked, {silent: true});
                this.$('.select').toggleClass('iconf-check').toggleClass('iconf-check-empty');
                App.vent.trigger('package:selection');
            }
        });
    });