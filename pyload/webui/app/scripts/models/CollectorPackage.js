define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'collections/LinkList'],
  function($, Backbone, _, App, Api, LinkList) {
    'use strict';
    return Backbone.Model.extend({

      idAttribute: 'name',
      defaults: {
        name: 'Unnamed package',
        password: null,
        new_name: null,
        links: null,
        pid: null,
        ignored: null // list of ignored plugins
      },

      initialize: function() {
        this.set('links', new LinkList());
        this.set('ignored', {});
      },

      destroy: function() {
        // Copied from backbones destroy method
        var model = this;
        model.trigger('destroy', model, model.collection);
      },

      // overwrites original name
      setName: function(name) {
        this.set('new_name', name);
      },

      // get the actual name
      getName: function() {
        var new_name = this.get('new_name');
        if (new_name)
          return new_name;

        return this.get('name');

      },
      // Add the package to pyload
      add: function() {
        var self = this;
        // Filter the ignored links and retrieve urls
        var links = _.map(this.get('links').filter(function(link) {
          return !_.has(self.get('ignored'), link.get('plugin'));
        }), function(link) {
          return link.get('url');
        });

        var pid = this.get('pid');

        if (pid !== null && _.isNumber(pid)) {
          console.log('Adding links to package', pid);
          $.ajax(App.apiRequest('addLinks',
            {
              pid: pid,
              links: links
            },
            {
              success: function() {
                self.destroy();
                App.vent.trigger('collectorPackage:added');
              }}));
        }
        else
          $.ajax(App.apiRequest('addPackage',
            {
              name: this.getName(),
              links: links,
              password: this.get('password')
            },
            {
              success: function() {
                self.destroy();
                App.vent.trigger('collectorPackage:added');
              }}));
      },

      updateLinks: function(links) {
        this.get('links').set(links, {remove: false});
        this.trigger('change');
      },

      // Returns true if pack is empty now
      removeLinks: function(links) {
        this.get('links').remove(_.map(links, function(link) {
          return link.url;
        }));
        return this.get('links').length === 0;
      },

      toJSON: function() {
        var data = {
          name: this.getName(),
          links: this.get('links').toJSON()
        };
        // Summary
        data.length = data.links.length;
        data.size = 0;
        data.online = 0;
        data.offline = 0;
        data.unknown = 0;
        data.plugins = {};

        // map of ignored plugins
        var ignored = this.get('ignored');

        _.each(data.links, function(link) {

          link.ignored = _.has(ignored, link.plugin);

          if (link.status === Api.DownloadStatus.Online)
            data.online++;
          else if (link.status === Api.DownloadStatus.Offline)
            data.offline++;
          else
            data.unknown++;

          if (link.size > 0)
            data.size += link.size;

          if (_.has(data.plugins, link.plugin))
            data.plugins[link.plugin].count++;
          else {
            data.plugins[link.plugin] = {
              count: 1,
              ignored: link.ignored
            };

          }

        });

        return data;
      }

    });
  });
