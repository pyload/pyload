define(['jquery', 'backbone', 'underscore', 'views/fileView', 'utils/lazyRequire'],
    function($, Backbone, _, fileView, lazyLoader) {

    // Renders a single package item
    return Backbone.View.extend({

        tagName: 'li',
        events: {
            'click .load': 'load',
            'click .delete': 'delete',
            'click .show-dialog': 'show'
        },

        modal: null,
        requireOnce: lazyLoader.once(),

        initialize: function() {
            this.model.on('change', this.render, this);
            this.model.on('remove', this.unrender, this);
        },

        render: function() {
            this.$el.html('Package ' + this.model.get('pid') + ': ' + this.model.get('name'));
            this.$el.append($('<a class="load" href="#"> Load</a>'));
            this.$el.append($('<a class="delete" href="#"> Delete</a>'));
            this.$el.append($('<a class="show-dialog" href="#"> Show</a>'));

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
        },

        show: function() {
            var self = this;
            this.requireOnce(['views/modal/modalView'], function(modalView){
                if (self.modal === null)
                    self.modal = new modalView();

                self.modal.show();
            });
         }
    });
});