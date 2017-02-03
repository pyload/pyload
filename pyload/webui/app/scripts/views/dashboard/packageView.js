define(['jquery', 'app', 'views/abstract/itemView', 'underscore', 'hbs!tpl/dashboard/package', 'hbs!tpl/dashboard/submenu'],
  function($, App, itemView, _, template, templateSubmenu) {
    'use strict';

    // Renders a single package item
    return itemView.extend({

      tagName: 'li',
      className: 'package-view',
      template: template,
      events: {
        'click .package-name, .btn-open': 'open',
        'click .icon-refresh': 'restart',
        'click .toggle-paused': 'pause',
        'click .select': 'select',
        'click .icon-chevron-down': 'loadMenu',
        'click .btn-delete': 'deleteItem',
        'click .btn-edit': 'edit',
        'click .btn-add': 'add',
        'click .dropdown-submenu a': 'invokeAddon'
      },

      // Ul for child packages (unused)
      ul: null,
      // Currently unused
      expanded: false,

      initialize: function() {
        this.listenTo(this.model, 'filter:added', this.hide);
        this.listenTo(this.model, 'filter:removed', this.show);
        this.listenTo(this.model, 'change', this.render);
        this.listenTo(this.model, 'remove', this.unrender);

        // Clear drop down menu
        var self = this;
        this.$el.on('mouseleave', function() {
          self.$('.dropdown-menu').parent().removeClass('open');
        });
      },

      onDestroy: function() {
      },

      // Render everything, optional only the fileViews
      render: function() {
        this.$el.html(this.template(this.model.toJSON()));
        this.$el.initTooltips();

        return this;
      },

      renderSubmenu: function(addons) {
        this.$('.dropdown-submenu ul').html(templateSubmenu(addons));
      },

      unrender: function() {
        itemView.prototype.unrender.apply(this);
        App.vent.trigger('package:destroyed', this.model);
      },

      // TODO:
      // Toggle expanding of packages
      expand: function(e) {
        e.preventDefault();
      },

      open: function(e) {
        e.preventDefault();
        App.dashboard.openPackage(this.model);
      },

      pause: function(e) {
        this.model.togglePaused();
      },

      select: function(e) {
        e.preventDefault();
        var checked = this.$('.select').hasClass('icon-check');
        // toggle class immediately, so no re-render needed
        this.model.set('selected', !checked, {silent: true});
        this.$('.select').toggleClass('icon-check').toggleClass('icon-check-empty');
        App.vent.trigger('package:selection');
      },

      edit: function() {
        var model = this.model;
        _.requireOnce(['views/dashboard/editPackageView'], function(ModalView) {
          new ModalView({model: model}).show();
        });
      },

      add: function() {
        App.vent.trigger('linkgrabber:open', this.model);
      },

      loadMenu: function() {
        App.addons.getForType(true, null, _.bind(this.renderSubmenu, this));
      },

      invokeAddon: function(e) {
        var el = $(e.target);
        // clicked on icon
        if (el.context.tagName === 'IMG')
          el = el.parent();

        App.addons.invoke(el.data('plugin'), el.data('func'), [this.model.get('pid')]);
      }

    });
  });
