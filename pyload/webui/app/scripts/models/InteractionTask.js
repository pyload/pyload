define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
  function($, Backbone, _, App, Api) {
    'use strict';

    return Backbone.Model.extend({

      idAttribute: 'iid',

      defaults: {
        iid: -1,
        type: null,
        input: null,
        default_value: null,
        title: '',
        description: '',
        plugin: '',
        // additional attributes
        result: ''
      },

      // Model Constructor
      initialize: function() {

      },

      save: function(options) {
        options = App.apiRequest('setInteractionResult/' + this.get('iid'),
          {result: this.get('result')}, options);

        return $.ajax(options);
      },

      isNotification: function() {
        return this.get('type') === Api.Interaction.Notification;
      },

      isCaptcha: function() {
        return this.get('type') === Api.Interaction.Captcha;
      }
    });
  });
