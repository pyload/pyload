define(['jquery', 'backbone', 'underscore', 'app', 'hbs!tpl/setup/welcome'],
    function($, Backbone, _, App, template) {
        'use strict';

        return Backbone.Marionette.ItemView.extend({

            name: 'Language',
            template: template,

            events: {
            },

            ui: {
            },

            onRender: function() {
            }

        });
    });