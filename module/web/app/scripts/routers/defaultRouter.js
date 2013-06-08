define(['jquery','backbone','views/headerView'], function($, Backbone, HeaderView){

    var Router = Backbone.Router.extend({

        initialize: function(){
            Backbone.history.start();
        },

        // All of your Backbone Routes (add more)
        routes: {

            // When there is no hash bang on the url, the home method is called
            '': 'home'

        },

        'home': function(){
            // Instantiating mainView and anotherView instances
            var headerView = new HeaderView();

            // Renders the mainView template
            headerView.render();

        }
    });

    // Returns the Router class
    return Router;
});