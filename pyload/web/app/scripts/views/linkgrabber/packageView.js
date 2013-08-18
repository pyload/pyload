define(['jquery', 'underscore', 'backbone', 'app', 'hbs!tpl/linkgrabber/package'],
    function($, _, Backbone, App, template) {
        'use strict';
        return Backbone.Marionette.ItemView.extend({

            tagName: 'div',
            className: 'row-fluid package',
            template: template,

            modelEvents: {
                change: 'render'
            },

            ui: {
                'table': 'table'
            },

            events: {
                'click .btn-expand': 'expand',
                'click .btn-add': 'addPackage',
                'click .btn-delete': 'deletePackage',
                'click .btn-mini': 'deleteLink'
            },

            expanded: false,

            serializeData: function() {
                var data = this.model.toJSON();
                data.expanded = this.expanded;
                return data;
            },

            addPackage: function() {
                this.model.add();
            },

            deletePackage: function() {
                this.model.destroy();
            },

            deleteLink: function(e) {
                var el = $(e.target);
                var id = parseInt(el.data('index'), 10);

                var model = this.model.get('links').at(id);
                if (model)
                    model.destroy();

                this.render();
            },

            expand: function() {
                this.expanded ^= true;
                this.ui.table.toggle();
            }

        });
    });