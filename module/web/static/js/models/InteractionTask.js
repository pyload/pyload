define(['jquery', 'backbone', 'underscore', 'utils/apitypes'],
    function($, Backbone, _, Api) {

        return Backbone.Model.extend({

            idAttribute: 'iid',

            defaults: {
                iid: -1,
                type: null,
                input: null,
                default_value: null,
                title: "",
                description: "",
                plugin: ""
            },

            // Model Constructor
            initialize: function() {

            },

            isNotification: function() {
                return this.get('type') === Api.Interaction.Notification;
            }
        });
    });