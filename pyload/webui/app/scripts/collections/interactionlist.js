define(['jquery', 'backbone', 'underscore', 'app', 'models/interactiontask'],
  function($, Backbone, _, App, InteractionTask) {
    'use strict';

    return Backbone.Collection.extend({

      model: InteractionTask,

      comparator: function(task) {
        return task.get('iid');
      },

      fetch: function(options) {
        options = App.apiRequest('getInteractionTasks/0', null, options);
        var self = this;
        options.success = function(data) {
          self.set(data);
        };

        return $.ajax(options);
      },

      toJSON: function() {
        var data = {queries: 0, notifications: 0};

        this.map(function(task) {
          if (task.isNotification())
            data.notifications++;
          else
            data.queries++;
        });

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
