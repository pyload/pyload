// Sets the require.js configuration for your application.
require.config({

    // XXX: To many dots in file breaks dependencies
    paths: {

        jquery: "libs/jquery-1.9.0",
        jqueryui: "libs/jqueryui",
        flot: "libs/jquery.flot-1.1",
        transit: "libs/jquery.transit-0.9.9",
        animate: "libs/jquery.animate-enhanced-0.99",
        omniwindow: "libs/jquery.omniwindow",
        bootstrap: "libs/bootstrap-2.2.2",

        underscore: "libs/lodash-1.0.rc3",
        backbone: "libs/backbone-0.9.10",
        wreqr: "libs/backbone.wreqr-0.1.0",
        handlebars: "libs/Handlebars-1.0rc1",

        // Plugins
        text: "libs/text-2.0.3",
        tpl: "../../templates"

    },

    // Sets the configuration for your third party scripts that are not AMD compatible
    shim: {

        "backbone": {
            deps: ["underscore", "jquery"],
            exports: "Backbone"  //attaches "Backbone" to the window object
        },
        "flot": ["jquery"],
        "transit": ["jquery"],
        "omniwindow": ["jquery"],
        "bootstrap": ["jquery"],
        "animate": ["jquery"],
    } // end Shim Configuration
});