define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'views/abstract/itemView'],
    function($, Backbone, _, App, Api, ItemView) {

        // Renders single file item
        return ItemView.extend({

            idAttribute: 'pid',
            tagName: 'li',
            template: _.compile($("#template-header-progress").html()),
            events: {
            },

            initialize: function() {
                this.listenTo(this.model, 'change', this.render);
                this.listenTo(this.model, 'remove', this.unrender);
            },

            onDestroy: function() {
            },

            render: function() {
                // TODO: icon
                // TODO: other states
                // TODO: non download progress
                // TODO: better progressbar rendering
                this.$el.css('background-image', 'url(icons/sdf)');
                this.$el.html(this.template(this.model.toJSON()));
                return this;
            }
        });
    });