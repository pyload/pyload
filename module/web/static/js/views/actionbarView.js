define(['jquery', 'backbone', 'underscore', 'app'],
    function($, Backbone, _, App) {

        // Renders the actionbar for the dashboard
        return Backbone.View.extend({
            el: 'ul.actionbar',

            events: {
            },

            initialize: function() {

                this.$('.search-query').typeahead({
                    minLength: 2,
                    source: this.getAutocompletion
                });

            },

            render: function() {
            },

            getAutocompletion: function() {
                return ["static", "autocompletion", "demo", "with", "some", "keywords",
                    "a very long proposal for autocompletion"];
            }
        });
    });