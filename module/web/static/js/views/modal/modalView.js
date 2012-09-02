define(['jquery', 'backbone', 'underscore', 'omniwindow'], function($, Backbone, _) {

    return Backbone.View.extend({

        events: {

        },

        dialog: null,

        initialize: function() {

        },

        render: function() {
            this.$el.addClass('modal');
            this.$el.addClass('modal-closed');
            this.$el.append(this.renderContent());
            this.$el.css({opacity: 0, scale: 0.7});
            $("body").append(this.el);

            this.dialog = this.$el.omniWindow({
                overlay: {
                    selector: '#modal-overlay',
                    hideClass: 'modal-closed',
                    animations: {
                        hide: function(subjects, internalCallback) {
                            subjects.overlay.fadeOut(400, function() {
                                internalCallback(subjects);
                            });
                        },
                        show: function(subjects, internalCallback) {
                            subjects.overlay.fadeIn(250, function() {
                                internalCallback(subjects);
                            });
                        }}},
                modal: {
                    hideClass: 'modal-closed',
                    animations: {
                        hide: function(subjects, internalCallback) {
                            subjects.modal.transition({opacity: 'hide', scale: 0.7}, 250, function() {
                                internalCallback(subjects);
                            });
                        },

                        show: function(subjects, internalCallback) {
                            subjects.modal.transition({opacity: 'show', scale: 1}, 250, function() {
                                internalCallback(subjects);
                            });
                        }}
                }});

            return this;
        },
        renderContent: function() {
            return $('<h1>Dialog</h1>');
        },

        show: function() {
            if (this.dialog === null)
                this.render();

            this.dialog.trigger('show');
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