define('default', ['require', 'backbone', 'jquery', 'app', 'router',
  'models/usersession', 'models/addon_handler', 'collections/progresslist'],
  function(require, Backbone, $, App, Router, UserSession, addon_handler, ProgressList) {
    'use strict';

    // Global ajax options
    var options = {
      statusCode: {
        401: function() {
          console.log('Not logged in');
          App.navigate('login');
        }
      },
      xhrFields: {withCredentials: true}
    };

    $.ajaxSetup(options);

    Backbone.ajax = function() {
      Backbone.$.ajaxSetup.call(Backbone.$, options);
      return Backbone.$.ajax.apply(Backbone.$, arguments);
    };

    // global available models / collections
    App.addons = new addon_handler();
    App.progressList = new ProgressList();

    $(function() {
      // load setup async
      if (window.setup === 'true') {
        require(['setup'], function(SetupRouter) {
          App.router = new SetupRouter();
          App.start();
        });
      } else {
        App.user = new UserSession();
        App.router = new Router();
        App.start();
      }
    });

    return App;
  });
