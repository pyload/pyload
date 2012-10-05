define(['jquery', 'views/abstract/itemView', 'underscore', 'views/fileView', 'utils/lazyRequire', 'flotpie'],
    function($, itemView, _, fileView, lazyLoader) {

    // Renders a single package item
    return itemView.extend({

        tagName: 'li',
        className: 'package-view',
        template: _.template($("#template-package").html()),
        events: {
            'click .load': 'load',
            'click .delete': 'delete',
            'click .show-dialog': 'show_dialog'
        },

        modal: null,
        requireOnce: lazyLoader.once(),

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
            this.$el.html(this.template(this.model.toJSON()));

            var data = [
             { label: "Series1", data: 30},
             { label: "Series2", data: 90}
             ];
            var pie = this.$('.package-graph');
            $.plot(pie, data,
                {
                    series: {
                        pie: {
                            radius: 1,
                            show: true,
                            label: {
                                show: false
                            },
                            offset: {
                              top: 0,
                              left: 0
                            }
                        }
                    },
                    legend: {
                        show: false
                    }
                });

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
        },

        show_dialog: function() {
            var self = this;
            this.requireOnce(['views/modal/modalView'], function(modalView){
                if (self.modal === null)
                    self.modal = new modalView();

                self.modal.show();
            });
         }
    });
});