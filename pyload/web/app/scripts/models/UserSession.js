define(['jquery', 'backbone', 'underscore',  'utils/apitypes', 'cookie'],
    function($, Backbone, _, Api) {
        'use strict';

        return Backbone.Model.extend({

            idAttribute: 'username',

            defaults: {
                username: null,
                permissions: null,
                session: null
            },

            // Model Constructor
            initialize: function() {
                this.set('session', $.cookie('beaker.session.id'));
            }
        });
    });