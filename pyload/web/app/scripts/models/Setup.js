define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
    function($, Backbone, _, App, Api) {
        'use strict';

        return Backbone.Model.extend({

            url: App.apiUrl('setup'),
            defaults: {
                lang: 'en',
                system: null,
                deps: null,
                user: null,
                password: null
            },

            fetch: function(options) {
                options || (options = {});
                options.url = App.apiUrl('setup');
                return Backbone.Model.prototype.fetch.call(this, options);
            },

            // will get a 409 on success
            submit: function(options) {
                options || (options = {});
                options.url = App.apiUrl('setup_done');
                options.data = {
                    user: this.get('user'),
                    password: this.get('password')
                };
                return Backbone.Model.prototype.fetch.call(this, options);
            }

        });
    });
