define(['jquery', 'backbone', 'underscore', 'omniwindow'], function($, Backbone, _) {
    'use strict';

    return Backbone.View.extend({

        events: {
            'click .btn-confirm': 'confirm',
            'click .btn-close': 'hide',
            'click .close': 'hide'
        },

        template: null,
        dialog: null,

        onHideDestroy: false,
        confirmCallback: null,

        initialize: function(template, confirm) {
            this.confirmCallback = confirm;
            var self = this;
            if (this.template === null) {
                if (template) {
                    this.template = template;
                    // When template was provided this is a temporary dialog
                    this.onHideDestroy = true;
                }
                else
                    require(['text!tpl/default/modal.html'], function(template) {
                        self.template = template;
                    });
            }

        },

        // TODO: whole modal stuff is not very elegant
        render: function() {
            this.$el.html(this.template(this.renderContent()));
            this.onRender();

            if (this.dialog === null) {
                this.$el.addClass('modal hide');
                this.$el.css({opacity: 0, scale: 0.7});

                var self = this;
                $('body').append(this.el);
                this.dialog = this.$el.omniWindow({
                    overlay: {
                        selector: '#modal-overlay',
                        hideClass: 'hide',
                        animations: {
                            hide: function(subjects, internalCallback) {
                                subjects.overlay.transition({opacity: 'hide', delay: 100}, 300, function() {
                                    internalCallback(subjects);
                                    self.onHide();
                                    if (self.onHideDestroy)
                                        self.destroy();
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
            }

            return this;
        },

        onRender: function() {

        },

        renderContent: function() {
            return {};
        },

        show: function() {
            if (this.dialog === null)
                this.render();

            this.dialog.trigger('show');

            this.onShow();
        },

        onShow: function() {

        },

        hide: function() {
            this.dialog.trigger('hide');
        },

        onHide: function() {

        },

        confirm: function() {
            if (this.confirmCallback)
                this.confirmCallback.apply();

            this.hide();
        },

        destroy: function() {
            this.$el.remove();
            this.dialog = null;
            this.remove();
        }

    });
});