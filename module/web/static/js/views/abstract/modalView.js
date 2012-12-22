define(['jquery', 'backbone', 'underscore', 'omniwindow'], function($, Backbone, _) {

    return Backbone.View.extend({

        events: {
            'click .btn-close': 'hide',
            'click .close': 'hide'
        },

        template: null,
        dialog: null,

        initialize: function() {
            var self = this;
            if (this.template === null) {
                require(['text!tpl/default/modal.html'], function(template) {
                    self.template = template;
                });
            }

        },

        render: function() {
            this.$el.html(this.template({ content: this.renderContent().html()}));
            this.$el.addClass('modal hide');
            this.$el.css({opacity: 0, scale: 0.7});
            $("body").append(this.el);

            this.dialog = this.$el.omniWindow({
                overlay: {
                    selector: '#modal-overlay',
                    hideClass: 'hide',
                    animations: {
                        hide: function(subjects, internalCallback) {
                            subjects.overlay.transition({opacity: 'hide', delay: 100}, 300, function() {
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
                            subjects.modal.transition({opacity: 'show', scale: 1, delay: 100}, 300, function() {
                                internalCallback(subjects);
                            });
                        }}
                }});

            return this;
        },
        renderContent: function() {
            return $('<h1>Content!</h1>');
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