define(['jquery', 'backbone', 'underscore', 'app', 'views/abstract/itemView'],
    function($, Backbone, _, App, ItemView) {

    // Renders single file item
    return ItemView.extend({

        tagName: 'li',
        className: 'file-view',
//        template: _.template($("#template-file").html()),
        template: _.compile($("#template-file").html()),
        events: {

        },

        initialize: function() {
            this.model.on('change', this.render, this);
            this.model.on('remove', this.destroy, this);
        },

        onDestroy: function() {
            this.model.off('change', this.render);
            this.model.off('remove', this.destroy);
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
            return this;
        }

    });
});