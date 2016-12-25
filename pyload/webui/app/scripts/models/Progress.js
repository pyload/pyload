define(['jquery', 'backbone', 'underscore', 'utils/apitypes'], function($, Backbone, _, Api) {
  'use strict';

  return Backbone.Model.extend({

    // generated, not submitted
    idAttribute: 'pid',

    defaults: {
      pid: -1,
      plugin: null,
      name: null,
      statusmsg: -1,
      eta: -1,
      done: -1,
      total: -1,
      owner: -1,
      type: 0,
      download: null
    },

    getPercent: function() {
      if (this.get('total') > 0)
        return Math.round(this.get('done') * 100 / this.get('total'));
      return  0;
    },

    // Model Constructor
    initialize: function() {

    },

    // Any time a model attribute is set, this method is called
    validate: function(attrs) {

    },

    toJSON: function(options) {
      var obj = Backbone.Model.prototype.toJSON.call(this, options);
      obj.percent = this.getPercent();
      obj.downloading = this.isDownload() && this.get('download').status === Api.DownloadStatus.Downloading;

      return obj;
    },

    isDownload : function() {
      return this.has('download');
    }

  });

});
