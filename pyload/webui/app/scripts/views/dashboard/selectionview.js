define(['jquery', 'backbone', 'underscore', 'app', 'hbs!tpl/dashboard/select'],
  function($, Backbone, _, App, template) {
    'use strict';

    // Renders context actions for selection packages and files
    return Backbone.Marionette.ItemView.extend({

      el: '#selection-area',
      template: template,

      events: {
        'click .icon-check': 'deselect',
        'click .icon-pause': 'pause',
        'click .icon-trash': 'trash',
        'click .icon-refresh': 'restart'
      },

      // Element of the action bar
      actionBar: null,
      // number of currently selected elements
      current: 0,

      initialize: function() {
        this.$el.calculateHeight().height(0);
        var render = _.bind(this.render, this);

        App.vent.on('dashboard:updated', render);
        App.vent.on('dashboard:filtered', render);
        App.vent.on('package:selection', render);
        App.vent.on('file:selection', render);
        App.vent.on('selection:toggle', _.bind(this.select_toggle, this));


        // API events, maybe better to rely on internal ones?
        App.vent.on('package:deleted', render);
        App.vent.on('file:deleted', render);
      },

      get_files: function(all) {
        var files = [];
        if (App.dashboard.files)
          if (all)
            files = App.dashboard.files.where({visible: true});
          else
            files = App.dashboard.files.where({selected: true, visible: true});

        return files;
      },

      get_packs: function() {
        if (!App.dashboard.tree.get('packages'))
          return []; // TODO:

        return App.dashboard.tree.get('packages').where({selected: true});
      },

      render: function() {
        var files = this.get_files().length;
        var packs = this.get_packs().length;

        if (files + packs > 0) {
          this.$el.html(this.template({files: files, packs: packs}));
          this.$el.initTooltips('bottom');
        }

        if (files + packs > 0 && this.current === 0)
          this.$el.slideOut();
        else if (files + packs === 0 && this.current > 0)
          this.$el.slideIn();

        // TODO: accessing ui directly, should be events
        if (files > 0) {
          App.actionbar.currentView.ui.select.addClass('icon-check').removeClass('icon-check-empty');
          App.dashboard.ui.packages.addClass('ui-files-selected');
        }
        else {
          App.actionbar.currentView.ui.select.addClass('icon-check-empty').removeClass('icon-check');
          App.dashboard.ui.packages.removeClass('ui-files-selected');
        }

        this.current = files + packs;
      },

      // Deselects all items
      deselect: function() {
        this.get_files().map(function(file) {
          file.set('selected', false);
        });

        this.get_packs().map(function(pack) {
          pack.set('selected', false);
        });

        this.render();
      },

      pause: function() {
        alert('Not implemented yet');
        this.deselect();
      },

      trash: function() {
        _.confirm('dialogs/confirm_delete', function() {

          var pids = [];
          // TODO: delete many at once
          this.get_packs().map(function(pack) {
            pids.push(pack.get('pid'));
            pack.destroy();
          });

          // get only the fids of non deleted packages
          var fids = _.filter(this.get_files(),function(file) {
            return !_.contains(pids, file.get('package'));
          }).map(function(file) {
              file.destroyLocal();
              return file.get('fid');
            });

          if (fids.length > 0)
            $.ajax(App.apiRequest('removeFiles', {fids: fids}));

          this.deselect();
        }, this);
      },

      restart: function() {
        this.get_files().map(function(file) {
          file.restart();
        });
        this.get_packs().map(function(pack) {
          pack.restart();
        });

        this.deselect();
      },

      // Select or deselect all visible files
      select_toggle: function() {
        var files = this.get_files();
        if (files.length === 0) {
          this.get_files(true).map(function(file) {
            file.set('selected', true);
          });

        } else
          files.map(function(file) {
            file.set('selected', false);
          });

        this.render();
      }
    });
  });
