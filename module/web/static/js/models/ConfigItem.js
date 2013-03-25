define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
    function($, Backbone, _, App, Api) {

        return Backbone.Model.extend({

            defaults: {
                name: "",
                label: "",
                description: "",
                input: null,
                default_valie: null,
                value: null,
                // additional attributes
                inputView: null
            },

            // Model Constructor
            initialize: function() {

            }
        });
    });