define(['jquery', 'backbone', 'underscore', 'models/File'], function($, Backbone, _, File) {
    'use strict';

    return Backbone.Collection.extend({

        model: File,

        comparator: function(file) {
            return file.get('fileorder');
        },

        initialize: function() {

        }

    });

});