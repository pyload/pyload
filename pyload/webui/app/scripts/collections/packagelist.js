define(['jquery', 'backbone', 'underscore', 'models/package'], function($, Backbone, _, Package) {
  'use strict';

  return Backbone.Collection.extend({

    model: Package,

    comparator: function(pack) {
      return pack.get('packageorder');
    },

    initialize: function() {
    }

  });
});
