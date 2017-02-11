define(['jquery', 'backbone', 'underscore'],
  function($, Backbone, _) {
    'use strict';

    return Backbone.Model.extend({

      defaults: {
        speed: 0,
        linkstotal: 0,
        linksqueue: 0,
        sizetotal: 0,
        sizequeue: 0,
        notifications: -1,
        paused: false,
        download: false,
        reconnect: false,
        quota: -1
      },

      // Model Constructor
      initialize: function() {

      },

      fetch: function(options) {
        options || (options = {});
        options.url = 'api/get_status_info';

        return Backbone.Model.prototype.fetch.call(this, options);
      },

      toJSON: function(options) {
        var obj = Backbone.Model.prototype.toJSON.call(this, options);

        obj.linksdone = obj.linkstotal - obj.linksqueue;
        obj.sizedone = obj.sizetotal - obj.sizequeue;
        if (obj.speed && obj.speed > 0)
          obj.eta = Math.round(obj.sizequeue / obj.speed);
        else if (obj.sizequeue > 0)
          obj.eta = Infinity;
        else
          obj.eta = 0;

        return obj;
      }

    });
  });
