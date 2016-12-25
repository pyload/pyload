// Sets the require.js configuration for your application.
'use strict';
require.config({

  deps: ['default'],

  paths: {
    jquery: '../modules/jquery/dist/jquery.min',
    flot: '../modules/Flot/jquery.flot',
    transit: '../modules/jquery.transit/jquery.transit',
    animate: '../modules/jQuery-Animate-Enhanced/jquery.animate-enhanced.min',
    cookie: '../modules/jquery.cookie/jquery.cookie',
    omniwindow: 'vendor/jquery.omniwindow',
    select2: '../modules/select2/select2',
    bootstrap: '../modules/bootstrap/dist/js/bootstrap.min',
    underscore: '../modules/underscore/underscore-min',
    backbone: '../modules/backbone/backbone-min',
    marionette: '../modules/backbone.marionette/lib/backbone.marionette.min',
    // version must be tested carefully, many are broken for amd
    handlebars: '../modules/handlebars.js/dist/handlebars',
    jed: '../modules/jed/jed',
    moment: '../modules/moment/moment',

    // TODO: Two hbs dependencies could be replaced
    // i18nprecompile: '../modules/require-handlebars-plugin/hbs/i18nprecompile',
    json2: '../modules/require-handlebars-plugin/hbs/json2',

    // Plugins
    // text: '../modules/requirejs-text/text',
    hbs: '../modules/require-handlebars-plugin/hbs',

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
    helperPathCallback:     // Callback to determine the path to look for helpers
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
