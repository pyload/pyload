define(['jquery', 'backbone', 'underscore', 'text!tpl/default/modal.html', 'omniwindow'], function($, Backbone, _, template) {

    return Backbone.View.extend({

        events: {
            'click .btn-close': 'hide',
            'click .close': 'hide'
        },

        template: _.template(template),

        dialog: null,

        initialize: function() {

        },

        render: function() {
            this.$el.html(this.template({ content: this.renderContent().html(), header: this.getHeader()}));
            this.$el.addClass('modal hide');
            this.$el.css({opacity: 0, scale: 0.7});
            $("body").append(this.el);

            this.dialog = this.$el.omniWindow({
                overlay: {
                    selector: '#modal-overlay',
                    hideClass: 'hide',
                    animations: {
                        hide: function(subjects, internalCallback) {
                            subjects.overlay.fadeOut(400, function() {
                                internalCallback(subjects);
                            });
                        },
                        show: function(subjects, internalCallback) {
                            subjects.overlay.fadeIn(300);
                            internalCallback(subjects);
                        }}},
                modal: {
                    hideClass: 'hide',
                    animations: {
                        hide: function(subjects, internalCallback) {
                            subjects.modal.transition({opacity: 'hide', scale: 0.7}, 300);
                            internalCallback(subjects);
                        },

                        show: function(subjects, internalCallback) {
                            subjects.modal.transition({opacity: 'show', scale: 1}, 400, function() {
                                internalCallback(subjects);
                            });
                        }}
                }});

            return this;
        },
        renderContent: function() {
            return $('<h1>Content!</h1>');
        },

        getHeader: function() {
            return 'Dialog';
        },

        show: function() {
            if (this.dialog === null)
                this.render();

            this.dialog.trigger('show');

            // TODO: set focus on first element
        },

        hide: function() {
            this.dialog.trigger('hide');
        },

        destroy: function() {
            this.$el.remove();
            this.dialog = null;
        }

    });
});