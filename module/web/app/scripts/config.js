// Sets the require.js configuration for your application.
'use strict';
require.config({

    deps: ['default'],

    paths: {

        jquery: '../components/jquery/jquery',
        flot: '../components/flot/jquery.flot',
        transit: '../components/jquery.transit/jquery.transit',
        animate: '../components/jquery.animate-enhanced/scripts/src/jquery.animate-enhanced',
        cookie: '../components/jquery.cookie/jquery.cookie',
        omniwindow: 'vendor/jquery.omniwindow',
        select2: '../components/select2/select2',
        bootstrap: 'vendor/bootstrap-2.3.2',
        underscore: '../components/underscore/underscore',
        backbone: '../components/backbone/backbone',
        marionette: '../components/backbone.marionette/lib/backbone.marionette',
//        handlebars: '../components/handlebars.js/dist/handlebars',
        handlebars: 'vendor/Handlebars-1.0rc1',
        jed: '../components/jed/jed',

        // TODO: Two hbs dependencies could be replaced
        i18nprecompile: '../components/require-handlebars-plugin/hbs/i18nprecompile',
        json2: '../components/require-handlebars-plugin/hbs/json2',

        // Plugins
        text: '../components/requirejs-text/text',
        hbs: '../components/require-handlebars-plugin/hbs',

        // Shortcut
        tpl: '../templates/default'
    },

    hbs: {
        disableI18n: true,
        helperPathCallback:       // Callback to determine the path to look for helpers
              function (name) {
                  // Some helpers are accumulated into one file
                  if (name.indexOf('file') === 0)
                    name = 'fileHelper';

                return 'helpers/' + name;
            },
        templateExtension: 'html'
    },

    // Sets the configuration for your third party scripts that are not AMD compatible
    shim: {
        underscore: {
            exports: '_'
        },

        backbone: {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },

        marionette: ['backbone'],
//        handlebars: {
//            exports: 'Handlebars'
//        },

        flot: ['jquery'],
        transit: ['jquery'],
        cookie: ['jquery'],
        omniwindow: ['jquery'],
        select2: ['jquery'],
        bootstrap: ['jquery'],
        animate: ['jquery']
    }
});