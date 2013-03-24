define(['jquery', 'underscore', 'app', 'views/abstract/modalView', 'text!tpl/default/queryDialog.html'],
    function($, _, App, modalView, template) {
        return modalView.extend({

            events: {
                'click .btn-success': 'submit',
                'submit form': 'submit'
            },

            model: null,
            parent: null,
            template: _.compile(template),

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

                if (this.model.isCaptcha()) {
                    var input = this.model.get('input').data;
                    data.captcha = input[0];
                    data.type = input[1];
                }

                return data;
            },

            submit: function(e) {
                e.stopPropagation();
                // TODO: different input types
                // TODO: load next task

                this.model.set('result', this.$('input').val());
                var self = this;
                this.model.save({success: function() {
                    self.hide();
                }});

                this.$('input').val('');
            },

            onShow: function() {
                this.$('input').focus();
            }

        });
    });