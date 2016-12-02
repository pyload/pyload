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

                    // set destination pid
                    if (self.model)
                        pack.set('pid', self.model.get('pid'));

                    // Remove links from other packages and delete empty ones
                    self.collection.each(function(pack2) {
                        console.log(pack2, links);
                        if (pack2 !== pack)
                            if (pack2.removeLinks(links))
                                self.collection.remove(pack2);
                    });

                    pack.updateLinks(links);
                });
            }
        });
    });
