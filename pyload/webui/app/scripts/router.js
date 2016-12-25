/**
 * Router defines routes that are handled by registered controller
 */
define([
  // Libraries
  'backbone',
  'marionette',

  // Modules
  'controller'
],
  function(Backbone, Marionette, Controller) {
    'use strict';

    return Backbone.Marionette.AppRouter.extend({

      appRoutes: {
        '': 'dashboard',
        'login': 'login',
        'logout': 'logout',
        'settings': 'settings',
        'accounts': 'accounts',
        'admin': 'admin'
      },

      // Our controller to handle the routes
      controller: Controller
    });
  });
