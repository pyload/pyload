/* 
 *  Global Application Object
 *  Contains all necessary logic shared across views
 */
/*jslint browser: true*/
define([

    // Libraries.
    'jquery',
    'underscore',
    'backbone',
    'utils/initHB',
    'utils/animations',
    'utils/lazyRequire',
    'utils/dialogs',
    'wreqr',
    'bootstrap',
    'animate'

], function($, _, Backbone, Handlebars) {
    'use strict';

    var Application = function(options){
        this.vent = new Backbone.Wreqr.EventAggregator();
        _.extend(this, options);
    };

    // Add Global Helper functions
    _.extend(Application.prototype, Backbone.Events, {

        // Generates options dict that can be used for xhr requests
        apiRequest: function(method, data, options) {
            options || (options = {});
            options.url = window.pathPrefix + "/api/" + method;
            options.dataType = "json";
            if (data) {
                options.type = "POST";
                options.data = {};
                // Convert arguments to json
                _.keys(data).map(function(key) {
                    options.data[key] = JSON.stringify(data[key]);
                });
            }

            return options;
        },

        openWebSocket: function(path) {
            return new WebSocket(window.wsAddress.replace('%s', window.location.hostname) + path);
        }
    });


    // Returns the app object to be available to other modules through require.js.
    return new Application();
});