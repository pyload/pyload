define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
  function($, Backbone, _, App, Api) {
    'use strict';

    return Backbone.Model.extend({

      // cache results for 1 min
      CACHE: 60 * 1000,

      defaults: {
        timestamp: 0,
        // dict with all addon handlers
        data: null
      },

      fetch: function(options) {
        return Backbone.Model.prototype.fetch.call(this,
          App.apiRequest('getAddonHandler', null, options));
      },

      parse: function(resp) {
        this.set('timestamp', new Date().getTime());
        return {data: resp};
      },

      // available addon handler for package or media types
      // async when callback is set
      getForType: function(pack, media, callback) {
        var self = this;

        if (callback && (!this.has('data') || this.get('timestamp') + this.CACHE < new Date().getTime())) {
          this.fetch({success: function() {
            callback(self.getForType(pack, media));
          }});
          return;
        }

        var addons = this.get('data');

        // TODO: filter accordingly

        if (_.isFunction(callback)) {
          callback(addons);
        }
        else {
          return addons;
        }
      },

      // dispatches call to the plugin
      invoke: function(plugin, func, args, success) {
        console.log('Invoking addon', plugin, func, args);
        return $.ajax(App.apiRequest('invokeAddon', {
          plugin: plugin,
          func: func,
          func_args: args
        }, {sucess: success}));
      }
    });
  });
