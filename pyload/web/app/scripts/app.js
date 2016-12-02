/*
 *  Global Application Object
 *  Contains all necessary logic shared across views
 */
define([

    // Libraries.
    'jquery',
    'underscore',
    'backbone',
    'handlebars',
    'utils/animations',
    'utils/lazyRequire',
    'utils/dialogs',
    'marionette',
    'bootstrap',
    'animate'

], function($, _, Backbone, Handlebars) {
    'use strict';

    Backbone.Marionette.TemplateCache.prototype.compileTemplate = function(rawTemplate) {
        return Handlebars.compile(rawTemplate);
    };

    // TODO: configurable root
    var App = new Backbone.Marionette.Application({
        root: '/'
    });

    App.addRegions({
        header: '#header',
        notification: '#notification-area',
        selection: '#selection-area',
        content: '#content',
        actionbar: '#actionbar'
    });

    App.navigate = function(url) {
        return Backbone.history.navigate(url, true);
    };

    App.apiUrl = function(path) {
        var prefix = window.pathPrefix;
        if (window.external !== 'false')
            prefix = window.hostProtocol + window.hostAddress + ':' + window.hostPort + prefix;

        return prefix + '/' + path;
    };

    // Add Global Helper functions
    // Generates options dict that can be used for xhr requests
    App.apiRequest = function(method, data, options) {
        options || (options = {});
        options.url = App.apiUrl('api/' + method);
        options.dataType = 'json';

        if (data) {
            options.type = 'POST';
            options.data = {};
            // Convert arguments to json
            _.keys(data).map(function(key) {
                options.data[key] = JSON.stringify(data[key]);
            });
        }

        return options;
    };

    App.setTitle = function(name) {
        var title = window.document.title;
        var newTitle;
        // page name separator
        var index = title.indexOf('-');
        if (index >= 0)
            newTitle = name + ' - ' + title.substr(index + 2, title.length);
        else
            newTitle = name + ' - ' + title;

        window.document.title = newTitle;
    };

    App.openWebSocket = function(path) {
        return new WebSocket(window.wsAddress.replace('%s', window.hostAddress) + path);
    };

    App.on('initialize:after', function() {
//        TODO pushState variable
        Backbone.history.start({
            pushState: false,
            root: App.root
        });

        // All links should be handled by backbone
        $(document).on('click', 'a[data-nav]', function(evt) {
            var href = { prop: $(this).prop('href'), attr: $(this).attr('href') };
            var root = location.protocol + '//' + location.host + App.root;
            if (href.prop.slice(0, root.length) === root) {
                evt.preventDefault();
                Backbone.history.navigate(href.attr, true);
            }
        });
    });

    // Returns the app object to be available to other modules through require.js.
    return App;
});