define(['jquery', 'underscore', 'backbone', 'app', 'models/ConfigHolder', './configSectionView',
  'hbs!tpl/settings/layout', 'hbs!tpl/settings/menu', 'hbs!tpl/settings/actionbar'],
  function($, _, Backbone, App, ConfigHolder, ConfigSectionView, template, templateMenu, templateBar) {
    'use strict';

    // Renders settings over view page
    return Backbone.Marionette.ItemView.extend({

      template: template,
      templateMenu: templateMenu,

      events: {
        'click .settings-menu li > a': 'change_section',
        'click .icon-remove': 'deleteConfig'
      },

      ui: {
        'menu': '.settings-menu',
        'content': '.setting-box > form'
      },

      selected: null,
      modal: null,

      coreConfig: null, // It seems collections are not needed
      pluginConfig: null,

      // currently open configHolder
      config: null,
      lastConfig: null,
      isLoading: false,

      initialize: function() {
        this.actionbar = Backbone.Marionette.ItemView.extend({
          template: templateBar,
          events: {
            'click .btn': 'choosePlugin'
          },
          choosePlugin: _.bind(this.choosePlugin, this)

        });
        this.listenTo(App.vent, 'config:open', this.openConfig);
        this.listenTo(App.vent, 'config:change', this.refresh);

        this.refresh();
      },

      refresh: function() {
        var self = this;
        $.ajax(App.apiRequest('getCoreConfig', null, {success: function(data) {
          self.pyloadConfig = data;
          self.renderMenu();
        }}));
        $.ajax(App.apiRequest('getPluginConfig', null, {success: function(data) {
          self.pluginConfig = data;
          self.renderMenu();
        }}));
      },

      onRender: function() {
        // set a height with css so animations will work
        this.ui.content.height(this.ui.content.height());
      },

      renderMenu: function() {
        var plugins = [],
          addons = [];

        // separate addons and default plugins
        // addons have an activated state
        _.each(this.pluginConfig, function(item) {
          if (item.activated === null)
            plugins.push(item);
          else
            addons.push(item);
        });

        this.$(this.ui.menu).html(this.templateMenu({
          core: this.coreConfig,
          plugin: plugins,
          addon: addons
        }));

        // mark the selected element
        this.$('li[data-name="' + this.selected + '"]').addClass('active');
      },

      openConfig: function(name) {
        // Do nothing when this config is already open
        if (this.config && this.config.get('name') === name)
          return;

        this.lastConfig = this.config;
        this.config = new ConfigHolder({name: name});
        this.loading();

        var self = this;
        this.config.fetch({success: function() {
          if (!self.isLoading)
            self.show();

        }, failure: _.bind(this.failure, this)});

      },

      loading: function() {
        this.isLoading = true;
        var self = this;
        this.ui.content.fadeOut({complete: function() {
          if (self.config.isLoaded())
            self.show();

          self.isLoading = false;
        }});

      },

      show: function() {
        // TODO animations are bit sloppy
        this.ui.content.css('display', 'block');
        var oldHeight = this.ui.content.height();

        // this will destroy the old view
        if (this.lastConfig)
          this.lastConfig.trigger('destroy');
        else
          this.ui.content.empty();

        // reset the height
        this.ui.content.css('height', '');
        // append the new element
        this.ui.content.append(new ConfigSectionView({model: this.config}).render().el);
        // get the new height
        var height = this.ui.content.height();
        // set the old height again
        this.ui.content.height(oldHeight);
        this.ui.content.animate({
          opacity: 'show',
          height: height
        });
      },

      failure: function() {
        // TODO
        this.config = null;
      },

      change_section: function(e) {
        // TODO check for changes
        // TODO move this into render?

        var el = $(e.target).closest('li');

        this.selected = el.data('name');
        this.openConfig(this.selected);

        this.ui.menu.find('li.active').removeClass('active');
        el.addClass('active');
        e.preventDefault();
      },

      choosePlugin: function(e) {
        var self = this;
        _.requireOnce(['views/settings/pluginChooserModal'], function(Modal) {
          if (self.modal === null)
            self.modal = new Modal();

          self.modal.show();
        });
      },

      deleteConfig: function(e) {
        e.stopPropagation();
        var el = $(e.target).parent().parent();
        var name = el.data('name');
        var self = this;
        $.ajax(App.apiRequest('deleteConfig', {plugin: name}, { success: function() {
          self.refresh();
        }}));
        return false;
      }

    });
  });
