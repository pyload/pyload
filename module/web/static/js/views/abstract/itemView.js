define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    // A view that is meant for temporary displaying
    // All events must be unbound in onDestroy
    return Backbone.View.extend({

        tagName: 'li',
        destroy: function() {
            this.undelegateEvents();
            this.unbind();
            if (this.onDestroy){
                this.onDestroy();
            }
            this.$el.removeData().unbind();
            this.remove();
        },


        hide: function() {
            this.$el.zapOut();
        },

        show: function() {
            this.$el.zapIn();
        },

        load: function() {
            this.model.fetch();
        },

        delete: function() {
            this.model.destroy();
        }

    });
});