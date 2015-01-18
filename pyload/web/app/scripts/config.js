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
        bootstrap: '../components/bootstrap/docs/assets/js/bootstrap',
        underscore: '../components/underscore/underscore',
        backbone: '../components/backbone/backbone',
        marionette: '../components/backbone.marionette/lib/backbone.marionette',
        // version must be tested carefully, many are broken for amd
        handlebars: '../components/handlebars.js/dist/handlebars',
        jed: '../components/jed/jed',
        moment: '../components/momentjs/moment',

        // TODO: Two hbs dependencies could be replaced
        i18nprecompile: '../components/require-handlebars-plugin/hbs/i18nprecompile',
        json2: '../components/require-handlebars-plugin/hbs/json2',

        // Plugins
//        text: '../components/requirejs-text/text',
        hbs: '../components/require-handlebars-plugin/hbs',

        // Shortcut
        tpl: '../templates/default'
    },

    map: {
        '*': {
            'Handlebars': 'handlebars'
        }
    },

    hbs: {
        disableI18n: true,
        helperPathCallback:       // Callback to determine the path to look for helpers
            function(name) {
                if (name === '_' || name === 'ngettext')
                    name = 'gettext';

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
        marionette: {
            deps: ['backbone'],
            exports: 'Backbone'
        },
        handlebars: {
            exports: 'Handlebars'
        },

        flot: ['jquery'],
        transit: ['jquery'],
        cookie: ['jquery'],
        omniwindow: ['jquery'],
        select2: ['jquery'],
        bootstrap: ['jquery'],
        animate: ['jquery']
    }
});
