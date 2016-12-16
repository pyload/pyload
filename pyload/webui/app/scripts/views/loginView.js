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

                var self = this;
                var data = this.ui.form.serialize();
                // set flag to load user representation
                data += '&user=true';
                var options = App.apiRequest('login', null, {
                    data: data,
                    type: 'post',
                    success: function(data) {
                        console.log('User logged in', data);
                        // TODO: go to last page
                        if (data) {
                            App.user.set(data);
                            App.user.save();
                            App.navigate('');
                        }
                        else {
                            self.wrongLogin();
                        }
                    },
                    error: function() {
                        self.wrongLogin();
                    }
                });

                $.ajax(options);
                return false;
            },

            // TODO: improve
            wrongLogin: function() {
                alert('Wrong login');
            }

        });
    });
