define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'models/package', 'hbs!tpl/dashboard/actionbar'],
  /*jslint -W040: false*/
  function($, Backbone, _, App, Api, Package, template) {
    'use strict';

    // Modified version of type ahead show, nearly the same without absolute positioning
    function show() {
      this.$menu
        .insertAfter(this.$element)
        .show();

      this.shown = true;
      return this;
    }

    // Renders the actionbar for the dashboard, handles everything related to filtering displayed files
    return Backbone.Marionette.ItemView.extend({

      events: {
        'click .li-check': 'toggle_selection',
        'click .filter-type': 'filter_type',
        'click .filter-state': 'switch_filter',
        'submit .form-search': 'search'
      },

      ui: {
        'search': '.search-query',
        'stateMenu': '.dropdown-toggle .state',
        'select': '.btn-check',
        'name': '.breadcrumb .active'
      },

      template: template,
      // Visible dl state
      state: null,
      // bit mask of filtered, thus not visible media types
      types: 0,

      initialize: function() {
        this.state = Api.DownloadState.All;

        // Apply the filter before the content is shown
        this.listenTo(App.vent, 'dashboard:contentReady', this.apply_filter);
        this.listenTo(App.vent, 'dashboard:updated', this.apply_filter);
        this.listenTo(App.vent, 'dashboard:updated', this.updateName);
      },

      onRender: function() {
        // use our modified method
        $.fn.typeahead.Constructor.prototype.show = show;
        this.ui.search.typeahead({
          minLength: 2,
          source: this.getSuggestions
        });

      },

      // TODO: app level api request
      search: function(e) {
        e.stopPropagation();
        var query = this.ui.search.val();
        this.ui.search.val('');

        var pack = new Package();
        // Overwrite fetch method to use a search
        // TODO: quite hackish, could be improved to filter packages
        //     or show performed search
        pack.fetch = function(options) {
          pack.search(query, options);
        };

        App.dashboard.openPackage(pack);
      },

      getSuggestions: function(query, callback) {
        $.ajax(App.apiRequest('searchSuggestions', {pattern: query}, {
          method: 'POST',
          success: function(data) {
            callback(data);
          }
        }));
      },

      switch_filter: function(e) {
        e.stopPropagation();
        var element = $(e.target);
        var state = parseInt(element.data('state'), 10);
        var menu = this.ui.stateMenu.parent().parent();
        menu.removeClass('open');

        if (state === Api.DownloadState.Finished) {
          menu.removeClass().addClass('dropdown finished');
        } else if (state === Api.DownloadState.Unfinished) {
          menu.removeClass().addClass('dropdown active');
        } else if (state === Api.DownloadState.Failed) {
          menu.removeClass().addClass('dropdown failed');
        } else {
          menu.removeClass().addClass('dropdown');
        }

        this.state = state;
        this.ui.stateMenu.text(element.text());
        this.apply_filter();
      },

      // Applies the filtering to current open files
      apply_filter: function() {
        if (!App.dashboard.files)
          return;

        var self = this;
        App.dashboard.files.map(function(file) {
          var visible = file.get('visible');
          if (visible !== self.is_visible(file)) {
            file.set('visible', !visible, {silent: true});
            file.trigger('change:visible', !visible);
          }
        });

        App.vent.trigger('dashboard:filtered');
      },

      // determine if a file should be visible
      // TODO: non download files
      is_visible: function(file) {
        // bit is set -> not visible
        if (file.get('media') & this.types)
          return false;

        if (this.state === Api.DownloadState.Finished)
          return file.isFinished();
        else if (this.state === Api.DownloadState.Unfinished)
          return file.isUnfinished();
        else if (this.state === Api.DownloadState.Failed)
          return file.isFailed();

        return true;
      },

      updateName: function() {
        // TODO:
//        this.ui.name.text(App.dashboard.package.get('name'));
      },

      toggle_selection: function() {
        App.vent.trigger('selection:toggle');
      },

      filter_type: function(e) {
        var el = $(e.target);
        var type = parseInt(el.data('type'), 10);

        // Bit is already set, so type is not visible, will become visible now
        if (type & this.types) {
          el.find('i').removeClass('icon-remove').addClass('icon-ok');
        } else { // type will be hidden
          el.find('i').removeClass('icon-ok').addClass('icon-remove');
        }

        this.types ^= type;

        this.apply_filter();
        return false;
      }

    });
  });
