define(['jquery', 'backbone', 'underscore', 'views/fileView'], function($, Backbone, _, fileView) {

    // Renders a single package item
    return Backbone.View.extend({

        tagName: 'li',
        events: {
            'click .load': 'load',
            'click .delete': 'delete'
        },

        initialize: function() {
            this.model.on('change', this.render, this);
            this.model.on('remove', this.unrender, this);
        },

        render: function() {
            this.$el.html('Package ' + this.model.get('pid') + ': ' + this.model.get('name'));
            this.$el.append($('<a class="load" href="#"> Load</a>'));
            this.$el.append($('<a class="delete" href="#"> Delete</a>'));

            if (this.model.isLoaded()) {
                var ul = $('<ul></ul>');
                this.model.get('files').each(function(file) {
                    ul.append(new fileView({model: file}).render().el);
                });
                this.$el.append(ul);
            }
            return this;
        },

        unrender: function() {
            this.$el.remove();
        },

        load: function() {
            this.model.fetch();
        },

        delete: function() {
            this.model.destroy();
        }

    });
});