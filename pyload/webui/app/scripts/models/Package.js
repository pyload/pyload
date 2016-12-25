define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'collections/FileList', 'require'],
  function($, Backbone, _, App, Api, FileList, require) {
    'use strict';

    return Backbone.Model.extend({

      idAttribute: 'pid',

      defaults: {
        pid: -1,
        name: null,
        folder: '',
        root: -1,
        owner: -1,
        site: '',
        comment: '',
        password: '',
        added: -1,
        tags: null,
        status: -1,
        shared: false,
        packageorder: -1,
        stats: null,
        fids: null,
        pids: null,
        files: null, // Collection
        packs: null, // Collection

        selected: false // For Checkbox
      },

      // Model Constructor
      initialize: function() {
      },

      toJSON: function(options) {
        var obj = Backbone.Model.prototype.toJSON.call(this, options);
        obj.percent = Math.round(obj.stats.linksdone * 100 / obj.stats.linkstotal);
        obj.paused = obj.status === Api.PackageStatus.Paused;

        return obj;
      },

      toServerJSON: function() {
        var obj = Backbone.Model.prototype.toJSON.call(this);
        return {
          pid: obj.pid,
          site: obj.site,
          comment: obj.comment,
          password: obj.password,
          '@class': 'PackageInfo'
        };
      },

      // Changes url + method and delegates call to super class
      fetch: function(options) {
        options = App.apiRequest(
          'getFileTree/' + this.get('pid'),
          {full: false},
          options);

        return Backbone.Model.prototype.fetch.call(this, options);
      },

      // Create a pseudo package und use search to populate data
      search: function(qry, options) {
        options = App.apiRequest(
          'findFiles',
          {pattern: qry},
          options);

        return Backbone.Model.prototype.fetch.call(this, options);
      },

      // sync some attributes with the server
      save: function(options) {
        options = App.apiRequest(
          'updatePackage',
          {pack: this.toServerJSON()},
          options);

        return Backbone.Model.prototype.fetch.call(this, options);
      },

      togglePaused: function() {
        var self = this;
        var paused = this.get('status') === Api.PackageStatus.Paused;

        $.ajax(App.apiRequest('setPackagePaused', {
          pid: this.get('pid'),
          paused: !paused
        }, {
          success: function(data) {
            console.log('New package status', data);
            self.set('status', data);
          }
        }));
      },

      destroy: function(options) {
        // TODO: Not working when using data?, array seems to break it
        options = App.apiRequest(
          'removePackages/[' + this.get('pid') + ']',
          null, options);
        options.method = 'post';

        console.log(options);

        return Backbone.Model.prototype.destroy.call(this, options);
      },

      restart: function(options) {
        options = App.apiRequest(
          'restartPackage',
          {pid: this.get('pid')},
          options);

        var self = this;
        options.success = function() {
          self.fetch();
        };
        return $.ajax(options);
      },

      parse: function(resp) {
        // Package is loaded from tree collection
        if (_.has(resp, 'root')) {
          if (!this.has('files'))
            resp.root.files = new FileList(_.values(resp.files));
          else
            this.get('files').set(_.values(resp.files));

          // circular dependencies needs to be avoided
          var PackageList = require('collections/PackageList');

          if (!this.has('packs'))
            resp.root.packs = new PackageList(_.values(resp.packages));
          else
            this.get('packs').set(_.values(resp.packages));

          return resp.root;
        }
        return Backbone.Model.prototype.parse.call(this, resp);
      },

      // Any time a model attribute is set, this method is called
      validate: function(attrs) {

      }

    });
  });
