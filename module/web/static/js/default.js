// Sets the require.js configuration for your application.
// Note: Config needs to be duplicated for mobile.js
require.config({

    // XXX: To many dots in file breaks dependencies
    paths:{

        jquery:"libs/jquery-1.8.0",
        jqueryui:"libs/jqueryui",
        flot:"libs/jquery.flot-1.1",
        flotpie: "libs/jquery.flot.pie",
        transit:"libs/jquery.transit-0.1.3",
        omniwindow: "libs/jquery.omniwindow",
        bootstrap: "libs/bootstrap-2.1.1",

        underscore:"libs/lodash-0.7.0",
        backbone:"libs/backbone-0.9.2",
//        handlebars: "libs/Handlebars-1.0rc1",

        // Plugins
//        hbs: "plugins/hbs-2.0.1",
        text:"plugins/text-2.0.3",
        tpl: "../../templates"

    },

    // Sets the configuration for your third party scripts that are not AMD compatible
    shim:{

        "backbone":{
            deps:["underscore", "jquery"],
            exports:"Backbone"  //attaches "Backbone" to the window object
        },
        "flot" : ["jquery"],
        "flotpie" : ["flot"],
        "transit" : ["jquery"],
        "omniwindow" : ["jquery"],
        "bootstrap" : ["jquery"]
    } // end Shim Configuration

    // Handlebar Configuration
//    hbs : {
//        templateExtension : 'hbs',
//        disableI18n : true
//    }
});

define('default', ['jquery', 'backbone', 'routers/defaultRouter', 'views/headerView', 'views/packageTreeView',
    'utils/animations', 'bootstrap'],
    function ($, Backbone, DefaultRouter, HeaderView, TreeView) {


    var init = function(){
        var view = new HeaderView();
        view.render();
    };

    var initPackageTree = function() {
        $(function() {
            var view = new TreeView();
            view.init();
        });
    };

   return {"init":init, "initPackageTree": initPackageTree};
});