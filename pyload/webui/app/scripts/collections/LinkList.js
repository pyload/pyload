define(['jquery', 'backbone', 'underscore', 'models/LinkStatus'], function($, Backbone, _, LinkStatus) {
    'use strict';

    return Backbone.Collection.extend({

        model: LinkStatus,

        comparator: function(link) {
            return link.get('name');
        }

    });

});
