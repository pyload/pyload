define(['jquery', 'underscore', 'backbone', 'app', '../abstract/itemView', '../input/inputRenderer',
  'hbs!tpl/settings/config', 'hbs!tpl/settings/configItem'],
  function($, _, Backbone, App, itemView, renderForm, template, templateItem) {
    'use strict';

    // Renders settings over view page
    return itemView.extend({

      tagName: 'div',

      template: template,

      // Will only render one time with further attribute updates
      rendered: false,

      events: {
        'click .btn-primary': 'submit',
        'click .btn-reset': 'reset'
      },

      initialize: function() {
        this.listenTo(this.model, 'destroy', this.destroy);
      },

      render: function() {
        if (!this.rendered) {
          this.$el.html(this.template(this.model.toJSON()));

          // initialize the popover
          this.$('.page-header a').popover({
            placement: 'left'
//            trigger: 'hover'
          });

          // Renders every single element
          renderForm(this.$('.control-content'),
            this.model.get('items'), templateItem,
            _.bind(this.render, this), this);

          this.rendered = true;
        }
        // Enable button if something is changed
        if (this.model.hasChanges())
          this.$('.btn-primary').removeClass('disabled');
        else
          this.$('.btn-primary').addClass('disabled');

        // Mark all inputs that are modified
        _.each(this.model.get('items'), function(item) {
          var input = item.get('inputView');
          var el = input.$el.parent().parent();
          if (item.isChanged())
            el.addClass('info');
          else
            el.removeClass('info');
        });

        return this;
      },

      onDestroy: function() {
        // TODO: correct cleanup after building up so many views and models
      },

      submit: function(e) {
        e.stopPropagation();
        // TODO: success / failure popups
        var self = this;
        this.model.save({success: function() {
          self.render();
          App.vent.trigger('config:change');
        }});

      },

      reset: function(e) {
        e.stopPropagation();
        // restore the original value
        _.each(this.model.get('items'), function(item) {
          if (item.has('inputView')) {
            var input = item.get('inputView');
            input.setVal(item.get('value'));
            input.render();
          }
        });
        this.render();
      }

    });
  });
