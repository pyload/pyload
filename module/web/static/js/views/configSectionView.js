define(['jquery', 'underscore', 'backbone', 'app', './input/inputLoader'],
    function($, _, Backbone, App, load_input) {

        // Renders settings over view page
        return Backbone.View.extend({

            tagName: 'div',

            template: _.compile($("#template-config").html()),
            templateItem: _.compile($("#template-config-item").html()),

            // Will only render one time with further attribute updates
            rendered: false,

            events: {
                'click .btn-primary': 'submit'
                // TODO cancel
            },

            initialize: function() {
            },

            // TODO: correct cleanup after building up so many views and models
            render: function() {
                if (!this.rendered) {
                    this.$el.html(this.template(this.model.toJSON()));

                    // TODO: only render one time, rest of the attributes set manually

                    // initialize the popover
                    this.$('.page-header a').popover({
                        placement: 'left',
                        trigger: 'hover'
                    });

                    var container = this.$('.control-content');
                    var self = this;
                    _.each(this.model.get('items'), function(item) {
                        var el = $('<div>').html(self.templateItem(item.toJSON()));
                        var inputView = load_input("todo");
                        var input = new inputView(item.get('input'), item.get('value'),
                            item.get('default_value'), item.get('description')).render();
                        item.set('inputView', input);

                        self.listenTo(input, 'change', _.bind(self.render, self));
                        el.find('.controls').append(input.el);
                        container.append(el);
                    });
                    this.rendered = true;
                }
                // Enable button if something is changed
                if (this.model.hasChanges())
                    this.$('.btn-primary').removeClass('disabled');
                else
                    this.$('.btn-primary').addClass('disabled');

                // Mark all inputs that are modified
                _.each(this.model.get('items'), function(item) {
                    var input = item.get('inputView');
                    var el = input.$el.parent().parent();
                    if (item.isChanged())
                        el.addClass('info');
                    else
                        el.removeClass('info');
                });

                return this;
            },

            submit: function() {

            }

        });
    });