/**
 * Router and controller used in setup mode
 */
define([
  // Libraries
  'backbone',
  'marionette',
  'app',

  // Views
  'views/setup/setupView'
],
  function(Backbone, Marionette, App, SetupView) {
    'use strict';

    return Backbone.Marionette.AppRouter.extend({

      appRoutes: {
        '': 'setup'
      },

      controller: {

        setup: function() {

          var view = new SetupView();
          App.actionbar.show(new view.actionbar());
          App.content.show(view);
        }

      }
    });
  });
