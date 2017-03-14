// Sets the require.js configuration for your application.
'use strict';
require.config({

  deps: ['default'],

  paths: {
    jquery: '../../node_modules/jquery/dist/jquery.min',
    flot: '../../node_modules/Flot/jquery.flot',
    transit: '../../node_modules/jquery.transit/jquery.transit',
    animate: '../../node_modules/jQuery-Animate-Enhanced/jquery.animate-enhanced.min',
    cookie: '../../node_modules/jquery.cookie/jquery.cookie',
    omniwindow: 'vendor/jquery.omniwindow',
    select2: '../../node_modules/select2/select2',
    bootstrap: '../../node_modules/bootstrap/dist/js/bootstrap.min',
    underscore: '../../node_modules/underscore/underscore-min',
    backbone: '../../node_modules/backbone/backbone-min',
    marionette: '../../node_modules/backbone.marionette/lib/backbone.marionette.min',
    // version must be tested carefully, many are broken for amd
    handlebars: '../../node_modules/handlebars.js/dist/handlebars',
    jed: '../../node_modules/jed/jed',
    moment: '../../node_modules/moment/moment',

    // TODO: Two hbs dependencies could be replaced
    // i18nprecompile: '../../node_modules/require-handlebars-plugin/hbs/i18nprecompile',
    json2: '../../node_modules/require-handlebars-plugin/hbs/json2',

    // Plugins
    // text: '../../node_modules/requirejs-text/text',
    hbs: '../../node_modules/require-handlebars-plugin/hbs',

    // Shortcut
    tpl: '../templates'
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
