define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
    function($, Backbone, _, App, Api) {
        'use strict';

        return Backbone.Model.extend({

            defaults: {
                lang: 'en',
                user: null,
                password: null
            }

        });
    });