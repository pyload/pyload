define(['jquery', 'backbone', 'underscore', 'models/Package'], function($, Backbone, _, Package) {

    return Backbone.Collection.extend({

        model: Package,

        comparator: function(pack) {
            return pack.get('packageorder');
        },

        initialize: function() {
        }

    });
});