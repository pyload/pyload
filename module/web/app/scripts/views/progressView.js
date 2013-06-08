define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'views/abstract/itemView',
    'hbs!tpl/header/progress', 'helpers/pluginIcon'],
    function($, Backbone, _, App, Api, ItemView, template, pluginIcon) {

        // Renders single file item
        return ItemView.extend({

            idAttribute: 'pid',
            tagName: 'li',
            template: template,
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
                this.$el.css('background-image', 'url('+ pluginIcon('todo') +')');
                this.$el.html(this.template(this.model.toJSON()));
                return this;
            }
        });
    });