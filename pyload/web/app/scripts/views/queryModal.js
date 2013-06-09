define(['jquery', 'underscore', 'app', 'views/abstract/modalView', './input/inputLoader', 'text!tpl/default/queryDialog.html'],
    function($, _, App, modalView, load_input, template) {
        'use strict';
        return modalView.extend({

            // TODO: submit on enter reloads the page sometimes
            events: {
                'click .btn-success': 'submit',
                'submit form': 'submit'
            },
            template: _.compile(template),

            // the notificationView
            parent: null,

            model: null,
            input: null,

            initialize: function() {
                // Inherit parent events
                this.events = _.extend({}, modalView.prototype.events, this.events);
            },

            renderContent: function() {
                var data = {
                    title: this.model.get('title'),
                    plugin: this.model.get('plugin'),
                    description: this.model.get('description')
                };

                var input = this.model.get('input').data;
                if (this.model.isCaptcha()) {
                    data.captcha = input[0];
                    data.type = input[1];
                }
                return data;
            },

            onRender: function() {
                // instantiate the input
                var input = this.model.get('input');
                var InputView = load_input(input);
                this.input = new InputView(input);
                // only renders after wards
                this.$('#inputField').append(this.input.render().el);
            },

            submit: function(e) {
                e.stopPropagation();
                // TODO: load next task

                this.model.set('result', this.input.getVal());
                var self = this;
                this.model.save({success: function() {
                    self.hide();
                }});

                this.input.clear();
            },

            onShow: function() {
                this.input.focus();
            },

            onHide: function() {
                this.input.destroy();
            }
        });
    });