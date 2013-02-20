define(['jquery', 'backbone', 'underscore', 'app', 'views/abstract/itemView'],
    function($, Backbone, _, App, ItemView) {

    // Renders single file item
    return ItemView.extend({

        tagName: 'li',
        className: 'file-view',
//        template: _.template($("#template-file").html()),
        template: _.compile($("#template-file").html()),
        events: {
            'click .checkbox': 'select'
        },

        initialize: function() {
            this.listenTo(this.model, 'change', this.render);
            this.listenTo(this.model, 'remove', this.destroy);
        },

        onDestroy: function() {
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
            return this;
        },

        select: function(e) {
            e.preventDefault();
            var checked = this.$('.checkbox').hasClass('checked');
            // toggle class immediately, so no re-render needed
            this.model.set('selected', !checked, {silent: true});
            this.$('.checkbox').toggleClass('checked');
            App.vent.trigger('file:selection');
        }

    });
});