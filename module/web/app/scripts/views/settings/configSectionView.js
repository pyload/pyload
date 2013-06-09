define(['jquery', 'underscore', 'backbone', 'app', '../abstract/itemView', '../input/inputLoader',
    'hbs!tpl/settings/config', 'hbs!tpl/settings/configItem'],
    function($, _, Backbone, App, itemView, load_input, template, templateItem) {
        'use strict';

        // Renders settings over view page
        return itemView.extend({

            tagName: 'div',

            template: template,
            templateItem: templateItem,

            // Will only render one time with further attribute updates
            rendered: false,

            events: {
                'click .btn-primary': 'submit',
                'click .btn-reset': 'reset'
            },

            initialize: function() {
                this.listenTo(this.model, 'destroy', this.destroy);
            },

            render: function() {
                if (!this.rendered) {
                    this.$el.html(this.template(this.model.toJSON()));

                    // initialize the popover
                    this.$('.page-header a').popover({
                        placement: 'left'
//                        trigger: 'hover'
                    });

                    var container = this.$('.control-content');
                    var self = this;
                    _.each(this.model.get('items'), function(item) {
                        var json = item.toJSON();
                        var el = $('<div>').html(self.templateItem(json));
                        var InputView = load_input(item.get('input'));
                        var input = new InputView(json).render();
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

            onDestroy: function() {
                // TODO: correct cleanup after building up so many views and models
            },

            submit: function(e) {
                e.stopPropagation();
                // TODO: success / failure popups
                var self = this;
                this.model.save({success: function() {
                    self.render();
                    App.settingsView.refresh();
                }});

            },

            reset: function(e) {
                e.stopPropagation();
                // restore the original value
                _.each(this.model.get('items'), function(item) {
                    if (item.has('inputView')) {
                        var input = item.get('inputView');
                        input.setVal(item.get('value'));
                        input.render();
                    }
                });
                this.render();
            }

        });
    });