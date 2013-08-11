define(['jquery', 'underscore', 'app', 'views/abstract/modalView', 'hbs!tpl/accounts/editAccount'],
    function($, _, App, modalView, template) {
        'use strict';
        return modalView.extend({

            events: {
                'click .btn-save': 'save',
                'submit form': 'save'
            },

            template: template,

            initialize: function() {
                // Inherit parent events
                this.events = _.extend({}, modalView.prototype.events, this.events);
            },

            onRender: function() {
            },

            save: function() {
                var password = this.$('#password').val();
                if (password !== '') {
                    this.model.setPassword(password);
                }

                this.hide();
                return false;
            },

            onShow: function() {
            },

            onHide: function() {
            }
        });
    });