define(['jquery', 'backbone', 'underscore', 'helpers/gettext', './inputview'], function($, Backbone, _, gettext, inputView) {
  'use strict';

  return inputView.extend({

    tagName: 'input',
    events: {
      'keyup': 'onChange',
      'focus': 'showTooltip',
      'focusout': 'hideTooltip'
    },

    renderInput: function() {
      this.$el.attr('disabled', 'on');
      this.$el.attr('type', 'text');
      this.$el.attr('name', 'textInput');

      if (this.default_value)
        this.$el.attr('placeholder', this.default_value);
      else
        this.$el.attr('placeholder', gettext('Please click on the right position in the captcha'));

      if (this.value)
        this.$el.val(this.value);

      return this;
    },

    onClick: function(x,y) {
      this.$el.val(x + ',' + y);
      this.onChange();
    },

    clear: function() {
      this.$el.val('');
    },

    onChange: function(e) {
      this.setVal(this.$el.val());
    }

  });
});
