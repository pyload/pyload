define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'collections/LinkList'],
    function($, Backbone, _, App, Api, LinkList) {
        'use strict';
        return Backbone.Model.extend({

            idAttribute: 'name',
            defaults: {
                name: 'Unnamed package',
                password: null,
                new_name: null,
                links: null
            },

            initialize: function() {
                this.set('links', new LinkList());
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
                var links = this.get('links').pluck('url');

                $.ajax(App.apiRequest('addPackage',
                    {name: this.getName(),
                        links: links,
                        password: this.get('password')},
                    {success: function() {
                        self.destroy();
                        App.vent.trigger('package:added');
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
                var links = this.get('links');
                data.length = links.length;
                data.size = 0;
                data.online = 0;
                data.offline = 0;
                data.unknown = 0;

                // Summary
                links.each(function(link) {
                    if (link.get('status') === Api.DownloadStatus.Online)
                        data.online++;
                    else if (link.get('status') === Api.DownloadStatus.Offline)
                        data.offline++;
                    else
                        data.unknown++;

                    if (link.get('size') > 0)
                        data.size += link.get('size');
                });

                return data;
            }

        });
    });