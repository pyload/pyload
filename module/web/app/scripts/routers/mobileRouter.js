define(['jquery','backbone', 'underscore'], function($, Backbone, _){

    return Backbone.Router.extend({

        initialize: function(){
            _.bindAll(this, "changePage");

            this.$el = $("#content");

            // Tells Backbone to start watching for hashchange events
            Backbone.history.start();

        },

        // All of your Backbone Routes (add more)
        routes: {

            // When there is no hash bang on the url, the home method is called
            '': 'home'

        },

        'home': function(){

            var self = this;

            $("#p1").fastClick(function(){
                self.changePage($("<div class='page' style='background-color: #9acd32;'><h1>Page 1</h1><br>some content<br>sdfdsf<br>sdffg<h3>oiuzz</h3></div>"));
            });

            $("#p2").bind("click", function(){
                self.changePage($("<div class='page' style='background-color: blue;'><h1>Page 2</h1><br>some content<br>sdfdsf<br><h2>sdfsdf</h2>sdffg</div>"));
            });

        },

        changePage: function(content){

            var oldpage = this.$el.find(".page");
            content.css({x: "100%"});
            this.$el.append(content);
            content.transition({x:0}, function(){
                window.setTimeout(function(){
                    oldpage.remove();
                }, 400);
            });

//            $("#viewport").transition({x: "100%"}, function(){
//                $("#viewport").html(content);
//                $("#viewport").transition({x: 0});
//            });
        }

    });
});