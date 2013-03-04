define(['jquery', 'backbone', 'underscore', 'utils/apitypes'], function($, Backbone, _, Api) {

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
            visible: true
        },


        // Model Constructor
        initialize: function() {

        },

        destroy: function() {

        },

        restart: function(options) {
            options || (options = {});
            options.url = 'api/restartFile/' + this.get('fid');

            return $.ajax(options);
        },

        // Any time a model attribute is set, this method is called
        validate: function(attrs) {

        },

        isDownload : function() {
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