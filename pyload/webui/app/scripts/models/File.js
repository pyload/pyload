define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'], function($, Backbone, _, App, Api) {
  'use strict';

  var Finished = [Api.DownloadStatus.Finished, Api.DownloadStatus.Skipped];
  var Failed = [Api.DownloadStatus.Failed, Api.DownloadStatus.Aborted, Api.DownloadStatus.TempOffline, Api.DownloadStatus.Offline];
  // Unfinished - Other

  return Backbone.Model.extend({

    idAttribute: 'fid',

    defaults: {
      fid: -1,
      name: null,
      package: -1,
      owner: -1,
      size: -1,
      status: -1,
      media: -1,
      added: -1,
      fileorder: -1,
      download: null,

      // UI attributes
      selected: false,
      visible: true,
      progress: 0,
      eta: 0
    },

    // Model Constructor
    initialize: function() {

    },

    fetch: function(options) {
      options = App.apiRequest(
        'getFileInfo',
        {fid: this.get('fid')},
        options);

      return Backbone.Model.prototype.fetch.call(this, options);
    },

    destroy: function(options) {
      // also not working when using data
      options = App.apiRequest(
        'removeFiles/[' + this.get('fid') + ']',
        null, options);
      options.method = 'post';

      return Backbone.Model.prototype.destroy.call(this, options);
    },

    // Does not send a request to the server
    destroyLocal: function(options) {
      this.trigger('destroy', this, this.collection, options);
    },

    restart: function(options) {
      options = App.apiRequest(
        'restartFile',
        {fid: this.get('fid')},
        options);

      return $.ajax(options);
    },

    // Any time a model attribute is set, this method is called
    validate: function(attrs) {

    },

    setDownloadStatus: function(status) {
      if (this.isDownload())
        this.get('download').status = status;
    },

    isDownload: function() {
      return this.has('download');
    },

    isFinished: function() {
      return _.indexOf(Finished, this.get('download').status) > -1;
    },

    isUnfinished: function() {
      return _.indexOf(Finished, this.get('download').status) === -1 && _.indexOf(Failed, this.get('download').status) === -1;
    },

    isFailed: function() {
      return _.indexOf(Failed, this.get('download').status) > -1;
    }

  });

});
