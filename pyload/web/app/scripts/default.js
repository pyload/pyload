define('default', ['backbone', 'jquery', 'app', 'router', 'models/UserSession'],
    function(Backbone, $, App, Router, UserSession) {
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

        $(function() {
            App.session = new UserSession();
            App.router = new Router();
            App.start();
        });

        return App;
    });