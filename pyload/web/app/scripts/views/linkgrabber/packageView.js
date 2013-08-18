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
                'name': '.name',
                'table': 'table'
            },

            events: {
                'click .btn-expand': 'expand',
                'click .name': 'renamePackage',
                'keyup .name input': 'saveName',
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

            addPackage: function(e) {
                e.stopPropagation();
                this.model.add();
                return false;
            },

            renamePackage: function() {
                this.ui.name.addClass('edit');
                this.ui.name.find('input').focus();
            },

            saveName: function(e) {
                if (e.keyCode === 13) {
                    this.model.setName(this.ui.name.find('input').val());
                }
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

            expand: function(e) {
                e.stopPropagation();
                this.expanded ^= true;
                this.ui.table.toggle();
                return false;
            }

        });
    });