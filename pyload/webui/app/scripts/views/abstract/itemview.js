define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {
  'use strict';

  // A view that is meant for temporary displaying
  // All events must be unbound in onDestroy
  return Backbone.View.extend({

    tagName: 'li',
    destroy: function() {
      this.undelegateEvents();
      this.unbind();
      if (this.onDestroy) {
        this.onDestroy();
      }
      this.$el.removeData().unbind();
      this.remove();
    },

    hide: function() {
      this.$el.slideUp();
    },

    show: function() {
      this.$el.slideDown();
    },

    unrender: function() {
      var self = this;
      this.$el.slideUp(function() {
        self.destroy();
      });
    },

    deleteItem: function(e) {
      if (e)
        e.stopPropagation();
      this.model.destroy();
    },

    restart: function(e) {
      if(e)
        e.stopPropagation();
      this.model.restart();
    }

  });
});
