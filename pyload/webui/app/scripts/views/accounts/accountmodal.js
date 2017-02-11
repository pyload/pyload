define(['jquery', 'underscore', 'app', 'views/abstract/modalview', 'hbs!tpl/dialogs/add_account', 'helpers/pluginicon', 'select2'],
  function($, _, App, modalView, template, pluginIcon) {
    'use strict';
    return modalView.extend({

      events: {
        'submit form': 'add',
        'click .btn-add': 'add'
      },
      template: template,
      plugins: null,
      select: null,

      initialize: function() {
        // Inherit parent events
        this.events = _.extend({}, modalView.prototype.events, this.events);
        var self = this;
        $.ajax(App.apiRequest('getAccountTypes', null, {success: function(data) {
          self.plugins = _.sortBy(data, function(item) {
            return item;
          });
          self.render();
        }}));
      },

      onRender: function() {
        // TODO: could be a separate input type if needed on multiple pages
        if (this.plugins)
          this.select = this.$('#pluginSelect').select2({
            escapeMarkup: function(m) {
              return m;
            },
            formatResult: this.format,
            formatSelection: this.format,
            data: {results: this.plugins, text: function(item) {
              return item;
            }},
            id: function(item) {
              return item;
            }
          });
      },

      onShow: function() {
      },

      onHide: function() {
      },

      format: function(data) {
        return '<img class="logo-select" src="' + pluginIcon(data) + '"> ' + data;
      },

      add: function(e) {
        e.stopPropagation();
        if (this.select) {
          var plugin = this.select.val(),
            login = this.$('#login').val(),
            password = this.$('#password').val(),
            self = this;

          $.ajax(App.apiRequest('createAccount', {
            plugin: plugin, loginname: login, password: password
          }, { success: function(data) {
            App.vent.trigger('account:updated', data);
            self.hide();
          }}));
        }
        return false;
      }
    });
  });
