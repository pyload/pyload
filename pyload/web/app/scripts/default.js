define('default', ['require', 'backbone', 'jquery', 'app', 'router',
    'models/UserSession', 'models/AddonHandler'],
    function(require, Backbone, $, App, Router, UserSession, AddonHandler) {
        'use strict';

        // Global ajax options
        var options = {
            statusCode: {
                401: function() {
                    console.log('Not logged in.');
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

        App.addons = new AddonHandler();

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