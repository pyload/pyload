define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {
  'use strict';

  // Renders input elements
  return Backbone.View.extend({

    tagName: 'input',

    input: null,
    value: null,
    description: null,
    default_value: null,

    // enables tooltips
    tooltip: true,

    initialize: function(options) {
      this.input = options.input;
      this.default_value = this.input.default_value;
      this.value = options.value;
      this.description = options.description;
    },

    render: function() {
      this.renderInput();
      // data for tooltips
      if (this.description && this.tooltip) {
        this.$el.data('content', this.description);
        // TODO: render default value in popup?
//        this.$el.data('title', "TODO: title");
        this.$el.popover({
          placement: 'right',
          trigger: 'hover'
//          delay: { show: 500, hide: 100 }
        });
      }

      return this;
    },

    // triggered by captcha clicks
    onClick: function(x,y) {

    },

    renderInput: function() {
      // Overwrite this
    },

    showTooltip: function() {
      if (this.description && this.tooltip)
        this.$el.popover('show');
    },

    hideTooltip: function() {
      if (this.description && this.tooltip)
        this.$el.popover('hide');
    },

    destroy: function() {
      this.undelegateEvents();
      this.unbind();
      if (this.onDestroy) {
        this.onDestroy();
      }
      this.$el.removeData().unbind();
      this.remove();
    },

    // focus the input element
    focus: function() {
      this.$el.focus();
    },

    // Clear the input
    clear: function() {

    },

    // retrieve value of the input
    getVal: function() {
      return this.value;
    },

    // the child class must call this when the value changed
    setVal: function(value) {
      this.value = value;
      this.trigger('change', value);
    }
  });
});
