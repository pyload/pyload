define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'views/abstract/itemview',
  'hbs!tpl/header/progress', 'hbs!tpl/header/progress_status', 'helpers/pluginicon'],
  function($, Backbone, _, App, Api, ItemView, template, templateStatus, pluginIcon) {
    'use strict';

    // Renders single file item
    return ItemView.extend({

      idAttribute: 'pid',
      tagName: 'li',
      template: template,
      events: {
      },

      // Last name
      name: null,

      initialize: function() {
        this.listenTo(this.model, 'change', this.update);
        this.listenTo(this.model, 'remove', this.unrender);
      },

      onDestroy: function() {
      },

      // Update html without re-rendering
      update: function() {
        if (this.name !== this.model.get('name')) {
          this.name = this.model.get('name');
          this.render();
        }

        this.$('.bar').width(this.model.getPercent() + '%');
        this.$('.progress-status').html(templateStatus(this.model.toJSON()));
      },

      render: function() {
        // TODO: icon
        // TODO: other states
        // TODO: non download progress
        this.$el.css('background-image', 'url(' + pluginIcon('todo') + ')');
        this.$el.html(this.template(this.model.toJSON()));
        return this;
      }
    });
  });
