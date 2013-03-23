define(['jquery', 'backbone', 'underscore', 'app', 'models/InteractionTask'],
    function($, Backbone, _, App, InteractionTask) {

        return Backbone.Collection.extend({

            model: InteractionTask,

            comparator: function(task) {
                return task.get('iid');
            },

            fetch: function(options) {
                options = App.apiRequest('getInteractionTasks/0');

                return Backbone.Collection.prototype.fetch.apply(this, options);
            },

            toJSON: function() {
                var data = {queries: 0, notifications: 0, empty: false};

                this.map(function(task) {
                    if (task.isNotification())
                        data.notifications++;
                    else
                        data.queries++;
                });

                if (!data.queries && !data.notifications)
                    data.empty = true;

                return data;
            },

            // a task is waiting for attention (no notification)
            hasTaskWaiting: function() {
                var tasks = 0;
                this.map(function(task) {
                    if (!task.isNotification())
                        tasks++;
                });

                return tasks > 0;
            }

        });

    });