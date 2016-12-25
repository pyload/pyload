define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
  function($, Backbone, _, App, Api) {
    'use strict';

    return Backbone.Model.extend({

      idAttribute: 'url',

      defaults: {
        name: '',
        size: -1,
        status: Api.DownloadStatus.Queued,
        plugin: '',
        hash: null
      },

      destroy: function() {
        var model = this;
        model.trigger('destroy', model, model.collection);
      }

    });
  });
