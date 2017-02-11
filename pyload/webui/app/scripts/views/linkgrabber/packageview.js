define(['jquery', 'underscore', 'backbone', 'app', 'hbs!tpl/linkgrabber/package'],
  function($, _, Backbone, App, template) {
    'use strict';
    return Backbone.Marionette.ItemView.extend({

      tagName: 'div',
      className: 'row-fluid package',
      template: template,

      modelEvents: {
        change: 'render'
      },

      ui: {
        'name': '.name',
        'table': 'table',
        'password': '.password'
      },

      events: {
        'click .btn-expand': 'expand',
        'click .name': 'renamePackage',
        'keyup .name input': 'saveName',
        'click .btn-add': 'addPackage',
        'click .btn-password': 'togglePassword',
        'click .btn-delete': 'deletePackage',
        'click .btn-mini': 'deleteLink',
        'click .plugin-item': 'togglePlugin'
      },

      expanded: false,

      serializeData: function() {
        var data = this.model.toJSON();
        data.expanded = this.expanded;
        return data;
      },

      addPackage: function(e) {
        e.stopPropagation();
        this.model.set('password', this.ui.password.val());
        this.model.add();
        return false;
      },

      renamePackage: function(e) {
        e.stopPropagation();

        this.ui.name.addClass('edit');
        this.ui.name.find('input').focus();

        var self = this;
        $(document).one('click', function() {
          self.ui.name.removeClass('edit');
          self.ui.name.focus();
        });

        return false;
      },

      saveName: function(e) {
        if (e.keyCode === 13) {
          this.model.setName(this.ui.name.find('input').val());
        }
      },

      deletePackage: function() {
        this.model.destroy();
      },

      deleteLink: function(e) {
        var el = $(e.target);
        var id = parseInt(el.data('index'), 10);

        var model = this.model.get('links').at(id);
        if (model)
          model.destroy();

        this.render();
      },

      expand: function(e) {
        e.stopPropagation();
        this.expanded ^= true;
        this.ui.table.toggle();
        return false;
      },

      togglePassword: function(e) {
        var el = $(e.target);
        el.find('i').toggleClass('icon-lock icon-unlock');
        this.ui.password.toggle();
      },

      togglePlugin: function(e) {
        var el = $(e.target);
        var plugin = el.data('plugin');
        var ignored = this.model.get('ignored');
        if (_.has(ignored, plugin))
          delete ignored[plugin];
        else
          ignored[plugin] = true;

        this.render();
      }

    });
  });
