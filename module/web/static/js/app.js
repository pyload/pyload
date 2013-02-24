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

        restartFailed: function(pids, options) {
            options || (options = {});
            options.url = 'api/restartFailed';
            $.ajax(options);
        }

    });


    // Returns the app object to be available to other modules through require.js.
    return new Application();
});