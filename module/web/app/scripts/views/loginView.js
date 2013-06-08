define(['jquery', 'backbone', 'underscore', 'app', 'hbs!tpl/login'],
    function($, Backbone, _, App, template) {
        'use strict';

        // Renders context actions for selection packages and files
        return Backbone.Marionette.ItemView.extend({
            template: template,

            events: {
                'submit form': 'login'
            },

            ui: {
                'form': 'form'
            },

            login: function(e) {
                e.stopPropagation();

                var options = App.apiRequest('login', null, {
                    data: this.ui.form.serialize(),
                    type : 'post',
                    success: function(data) {
                        // TODO: go to last page, better error
                        if (data)
                            App.navigate('');
                        else
                            alert('Wrong login');
                    }
                });

                $.ajax(options);
                return false;
            }

        });
    });