define(['jquery', 'backbone', 'underscore', 'app', 'collections/InteractionList'],
    function($, Backbone, _, App, InteractionList) {

        // Renders context actions for selection packages and files
        return Backbone.View.extend({
            el: '#notification-area',
            template: _.compile($("#template-notification").html()),

            events: {
                'click .btn-query': 'openQuery',
                'click .btn-notification': 'openNotifications'
            },

            tasks: null,
            // current open task
            current: null,
            // area is slided out
            visible: false,

            initialize: function() {
                this.tasks = new InteractionList();

                this.$el.calculateHeight().height(0);

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

            render: function() {
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

            },

            openNotifications: function() {

            }
        });
    });