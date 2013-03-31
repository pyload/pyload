define(['jquery', 'underscore', 'backbone', 'app', '../abstract/itemView'],
    function($, _, Backbone, App, itemView) {

        // Renders settings over view page
        return itemView.extend({

            el: "tr",
            template: _.compile($('#template-account').html()),

            events: {
                'click .btn-danger': 'deleteItem'
            },

            initialize: function() {
                this.listenTo(this.model, 'remove', this.unrender);
                this.listenTo(App.vent, 'accounts:destroyContent', this.destroy);
            },

            render: function() {
                this.$el.html(this.template(this.model.toJSON()));
                return this;
            }
        });
    });