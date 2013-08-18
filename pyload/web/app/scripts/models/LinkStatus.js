define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
    function($, Backbone, _, App, Api) {
        'use strict';

        return Backbone.Model.extend({

            idAttribute: 'url',

            defaults: {
                name: '',
                plugin: '',
                size: -1,
                status: Api.DownloadStatus.Queued
            },

            destroy: function() {
                var model = this;
                model.trigger('destroy', model, model.collection);
            }

        });
    });