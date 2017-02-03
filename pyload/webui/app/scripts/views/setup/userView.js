define(['jquery', 'backbone', 'underscore', 'app', 'hbs!tpl/setup/user'],
  function($, Backbone, _, App, template) {
    'use strict';

    return Backbone.Marionette.ItemView.extend({

      name: 'User',
      template: template,

      events: {
        'click .btn-blue': 'submit'
      },

      ui: {
        username: '#username',
        password: '#password',
        password2: '#password2'
      },

      onRender: function() {
      },

      submit: function() {
        var pw = this.ui.password.val();
        var pw2 = this.ui.password2.val();

        // TODO: more checks and error messages
        if (pw !== pw2) {
          return;
        }

        this.model.set('user', this.ui.username.val());
        this.model.set('password', pw);

        this.model.trigger('page:next');
      }

    });
  });
