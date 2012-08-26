// Sets the require.js configuration for your application.
// Note: Config needs to be duplicated for mobile.js
require.config({

    // XXX: To many dots in file breaks dependencies
    paths:{

        jquery:"libs/jquery-1.8.0",
        jqueryui:"libs/jqueryui",
        flot:"libs/jquery.flot.min",
        omniwindow: "libs/jquery.omniwindow",

        underscore:"libs/lodash-0.5.2",
        backbone:"libs/backbone-0.9.2",

        // Require.js Plugins
        text:"plugins/text-2.0.3"

    },

    // Sets the configuration for your third party scripts that are not AMD compatible
    shim:{

        "backbone":{
            deps:["underscore", "jquery"],
            exports:"Backbone"  //attaches "Backbone" to the window object
        },
        "flot" : ["jquery"],
        "omniwindow" : ["jquery"]
    } // end Shim Configuration

});

define('default', ['jquery', 'backbone', 'routers/defaultRouter', 'views/headerView'], function ($, Backbone, DefaultRouter, HeaderView) {

    var init = function(){
        var view = new HeaderView();
        view.render();
    };

   return {"init":init};
});