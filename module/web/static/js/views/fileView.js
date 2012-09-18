define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    // Renders single file item
    return Backbone.View.extend({

        tagName: 'li',
        events: {

        },

        initialize: function() {
        },

        render: function() {
            this.$el.html(this.model.get('name'));
            return this;
        }

    });
});