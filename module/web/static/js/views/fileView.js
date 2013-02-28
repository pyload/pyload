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
                this.listenTo(this.model, 'change:visible', this.visibility_changed);
                this.listenTo(this.model, 'remove', this.destroy);
            },

            onDestroy: function() {
            },

            render: function() {
                var data = this.model.toJSON();
                if (data.download) {
                    var status = data.download.status;
                    // TODO: remove hardcoded states
                    if (status === 1 || status === 11)
                        data.offline = true;
                    else if (status === 7)
                        data.failed = true;
                    else if (status === 2)
                        data.online = true;
                    else if (status === 9)
                        data.waiting = true;
                    else if (status === 10)
                        data.downloading = true;
                    else if (status === 5 || status === 6)
                        data.finished = true;
                }

                this.$el.html(this.template(data));
                if (this.model.get('selected'))
                    this.$el.addClass('ui-selected');
                else
                    this.$el.removeClass('ui-selected');

                if (this.model.get('visible'))
                    this.$el.show();
                else
                    this.$el.hide();

                return this;
            },

            select: function(e) {
                e.preventDefault();
                var checked = this.$el.hasClass('ui-selected');
                // toggle class immediately, so no re-render needed
                this.model.set('selected', !checked, {silent: true});
                this.$el.toggleClass('ui-selected');
                App.vent.trigger('file:selection');
            },

            visibility_changed: function() {

            }

        });
    });