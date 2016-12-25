define(['jquery', 'backbone', 'underscore', 'models/Progress'], function($, Backbone, _, Progress) {
  'use strict';

  return Backbone.Collection.extend({

    model: Progress,

    comparator: function(progress) {
      return progress.get('eta');
    },

    initialize: function() {

    },

    // returns all progresses, that bit matches the given type
    // types have to be or'ed
    byType: function(types) {
      return this.filter(function(progress) {
        return (progress.get('type') & types) !== 0;
      });
    }

  });

});
