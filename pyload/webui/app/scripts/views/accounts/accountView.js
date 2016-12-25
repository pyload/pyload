define(['jquery', 'underscore', 'backbone', 'app', 'hbs!tpl/accounts/account'],
  function($, _, Backbone, App, template) {
    'use strict';

    return Backbone.Marionette.ItemView.extend({

      tagName: 'div',
      className: 'row-fluid',
      template: template,

      events: {
        'click .btn-success': 'toggle',
        'click .btn-blue': 'edit',
        'click .btn-yellow': 'refresh',
        'click .btn-danger': 'deleteAccount'
      },

      modelEvents: {
        'change': 'render'
      },

      modal: null,

      toggle: function() {
        this.model.set('activated', !this.model.get('activated'));
        this.model.save();
      },

      edit: function() {
        // TODO: clean the modal on view close
        var self = this;
        _.requireOnce(['views/accounts/accountEdit'], function(Modal) {
          if (self.modal === null)
            self.modal = new Modal({model: self.model});

          self.modal.show();
        });
      },

      refresh: function() {
        this.model.fetch({refresh: true});
      },

      deleteAccount: function() {
        this.model.destroy();
      }
    });
  });
