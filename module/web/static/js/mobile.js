// Sets the require.js configuration for your application.
require.config({

    paths:{

        jquery:"libs/jquery-1.8.0",
        jqueryui:"libs/jqueryui",
        flot:"libs/jquery.flot.min",
        transit:"libs/jquery.transit-0.1.3",
        fastClick:"libs/jquery.fastClick-0.2",
        omniwindow: "libs/jquery.omniwindow",

        underscore:"libs/lodash-0.7.0",
        backbone:"libs/backbone-0.9.2",

        // Require.js Plugins
        text:"plugins/text-2.0.3"

    },

  // Sets the configuration for your third party scripts that are not AMD compatible
  shim: {

      "backbone": {
          deps: ["underscore", "jquery"],
          exports: "Backbone"  //attaches "Backbone" to the window object
      },
      transit: ["jquery"],
      fastClick: ["jquery"]

  } // end Shim Configuration
  
});

define('mobile', ['routers/mobileRouter', 'transit', 'fastClick'], function(Mobile) {

    var init = function(){
        var router = new Mobile();
    };

    return {"init":init};
});
