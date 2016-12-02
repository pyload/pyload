define(['jquery', 'backbone', 'underscore', 'models/File'], function($, Backbone, _, File) {
    'use strict';

    return Backbone.Collection.extend({

        model: File,

        comparator: function(file) {
            return file.get('fileorder');
        },

        isEqual: function(fileList) {
            if (this.length !== fileList.length) return false;

            // Assuming same order would be faster in false case
            var diff = _.difference(this.models, fileList.models);

            // If there is a difference models are unequal
            return diff.length > 0;
        },

        initialize: function() {

        }

    });

});
