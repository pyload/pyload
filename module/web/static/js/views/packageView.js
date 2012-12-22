define(['jquery', 'views/abstract/itemView', 'underscore', 'views/fileView'],
    function($, itemView, _, fileView) {

    // Renders a single package item
    return itemView.extend({

        tagName: 'li',
        className: 'package-view',
        template: _.compile($("#template-package").html()),
        events: {
            'click .package-header': 'load',
            'click .delete': 'delete'
        },

        initialize: function() {
            this.model.on('filter:added', this.hide, this);
            this.model.on('filter:removed', this.show, this);
            this.model.on('change', this.render, this);
            this.model.on('remove', this.unrender, this);
        },

        onDestroy: function() {
            this.model.off('filter:added', this.hide); // TODO
        },

        render: function() {

            // TODO: on expanding don't re-render
            this.$el.html(this.template(this.model.toJSON()));

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
            var self = this;
            this.$el.zapOut(function() {
                self.destroy();
            });
        }
    });
});