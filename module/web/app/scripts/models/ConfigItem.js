define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
    function($, Backbone, _, App, Api) {
        'use strict';

        return Backbone.Model.extend({

            defaults: {
                name: '',
                label: '',
                description: '',
                input: null,
                default_value: null,
                value: null,
                // additional attributes
                inputView: null
            },

            // Model Constructor
            initialize: function() {

            },

            isChanged: function() {
                return this.get('inputView') && this.get('inputView').getVal() !== this.get('value');
            },

            // set new value and return json
            prepareSave: function() {
                // set the new value
                if (this.get('inputView'))
                    this.set('value', this.get('inputView').getVal());

                var data = this.toJSON();
                delete data.inputView;
                delete data.description;

                return data;
            }
        });
    });