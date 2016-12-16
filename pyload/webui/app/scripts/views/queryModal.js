define(['jquery', 'underscore', 'app', 'utils/apitypes', 'views/abstract/modalView', './input/inputLoader', 'hbs!tpl/dialogs/interactionTask'],
    function($, _, App, Api, modalView, load_input, template) {
        'use strict';
        return modalView.extend({

            className: 'query-modal',

            events: {
                'click #captchaImage': 'onClick',
                'click .btn-success': 'submit',
                'submit form': 'submit'
            },
            template: template,

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
                this.input = new InputView({input: input});
                if (input.type == Api.InputType.Click)
                    this.$('#captchaImage').css('cursor', 'crosshair');

                // only renders after wards
                this.$('#inputField').append(this.input.render().el);
            },

            onClick: function(e) {
                var el = $(e.target);
                var posX = el.offset().left,
                    posY = el.offset().top;

                 // TODO: calculate image size, scale positions to displayed / real image size
                this.input.onClick(Math.round(e.pageX - posX), Math.round(e.pageY - posY));
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
                return false;
            },

            onShow: function() {
                this.input.focus();
            },

            onHide: function() {
                this.input.destroy();
            }
        });
    });
