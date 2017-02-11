define(['jquery', 'backbone', 'underscore', 'app', 'hbs!tpl/setup/finished'],
  function($, Backbone, _, App, template) {
    'use strict';

    return Backbone.Marionette.ItemView.extend({

      name: 'Finished',
      template: template,

      events: {
        'click .btn-blue': 'confirm'
      },

      ui: {
      },

      onRender: function() {
      },

      confirm: function() {
        this.model.submit();
      }

    });
  });
