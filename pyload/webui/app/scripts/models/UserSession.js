define(['jquery', 'backbone', 'underscore', 'utils/apitypes', 'app'],
    function($, Backbone, _, Api, App) {
        'use strict';

        // Used in app -> can not have a dependency on app
        return Backbone.Model.extend({

            idAttribute: 'name',

            defaults: {
                uid: -1,
                name: 'User',
                permissions: null,
                session: null
            },

            // Model Constructor
            initialize: function() {
                this.set(JSON.parse(localStorage.getItem('user')));
            },

            save: function() {
                localStorage.setItem('user', JSON.stringify(this.toJSON()));
            },

            destroy: function() {
                localStorage.removeItem('user');
            },

            // TODO
            fetch: function(options) {
                options = App.apiRequest('todo', null, options);

                return Backbone.Model.prototype.fetch.call(this, options);
            }

        });
    });
