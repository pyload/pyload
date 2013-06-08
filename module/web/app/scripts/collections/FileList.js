define(['jquery', 'backbone', 'underscore', 'models/File'], function($, Backbone, _, File) {

    return Backbone.Collection.extend({

        model: File,

        comparator: function(file) {
            return file.get('fileorder');
        },

        initialize: function() {

        }

    });

});