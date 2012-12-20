define(['jquery', 'backbone', 'underscore', 'models/Progress'], function($, Backbone, _, Progress) {

    return Backbone.Collection.extend({

        model: Progress,

        comparator: function(progress) {
            return progress.get('eta');
        },

        initialize: function() {

        }

    });

});