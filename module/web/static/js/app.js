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
    'wreqr',
    'bootstrap'

], function($, _, Backbone, Handlebars) {
    'use strict';

    var Application = function(options){
        this.vent = new Backbone.Wreqr.EventAggregator();
        _.extend(this, options);
    };

    _.extend(Application.prototype, Backbone.Events, {


    });


    // Returns the app object to be available to other modules through require.js.
    return new Application();
});