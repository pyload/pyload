define(['jquery', 'underscore', 'backbone', 'app', './packageView'],
    function($, _, Backbone, App, packageView) {
        'use strict';
        return Backbone.Marionette.CollectionView.extend({
            itemView: packageView,
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