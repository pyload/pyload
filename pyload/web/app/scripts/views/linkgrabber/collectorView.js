define(['jquery', 'underscore', 'backbone', 'app', './packageView'],
    function($, _, Backbone, App, packageView) {
        'use strict';
        return Backbone.Marionette.CollectionView.extend({
            itemView: packageView,

            initialize: function() {
                this.listenTo(App.vent, 'linkcheck:updated', _.bind(this.onData, this));
            },

            onData: function(rid, result) {
                this.updateData({data: result});
            },

            updateData: function(result) {
                var self = this;
                _.each(result.data, function(links, name) {
                    var pack = self.collection.get(name);
                    if (!pack) {
                        pack = new self.collection.model({name: name});
                        self.collection.add(pack);
                    }

                    // TODO: remove links from all other packages than pack
                    pack.updateLinks(links);
                });
            }
        });
    });