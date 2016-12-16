define(['jquery', 'backbone', 'underscore', 'app', 'collections/InteractionList', 'hbs!tpl/notification'],
    function($, Backbone, _, App, InteractionList, template) {
        'use strict';

        // Renders context actions for selection packages and files
        return Backbone.Marionette.ItemView.extend({

            // Only view for this area so it's hardcoded
            el: '#notification-area',
            template: template,

            events: {
                'click .btn-query': 'openQuery',
                'click .btn-notification': 'openNotifications'
            },

            tasks: null,
            // area is slided out
            visible: false,
            // the dialog
            modal: null,

            initialize: function() {
                this.tasks = new InteractionList();

                App.vent.on('interaction:added', _.bind(this.onAdd, this));
                App.vent.on('interaction:deleted', _.bind(this.onDelete, this));

                var render = _.bind(this.render, this);
                this.listenTo(this.tasks, 'add', render);
                this.listenTo(this.tasks, 'remove', render);

            },

            onAdd: function(task) {
                this.tasks.add(task);
            },

            onDelete: function(task) {
                this.tasks.remove(task);
            },

            onRender: function() {
                this.$el.calculateHeight().height(0);
            },

            render: function() {

                // only render when it will be visible
                if (this.tasks.length > 0)
                    this.$el.html(this.template(this.tasks.toJSON()));

                if (this.tasks.length > 0 && !this.visible) {
                    this.$el.slideOut();
                    this.visible = true;
                }
                else if (this.tasks.length === 0 && this.visible) {
                    this.$el.slideIn();
                    this.visible = false;
                }

                return this;
            },

            openQuery: function() {
                var self = this;

                _.requireOnce(['views/queryModal'], function(ModalView) {
                    if (self.modal === null) {
                        self.modal = new ModalView();
                        self.modal.parent = self;
                    }

                    self.modal.model = self.tasks.at(0);
                    self.modal.render();
                    self.modal.show();
                });

            },

            openNotifications: function() {

            }
        });
    });
