define(['jquery', 'backbone', 'underscore', 'models/TreeCollection', 'views/packageView', 'views/fileView'],
    function($, Backbone, _, TreeCollection, packageView, fileView) {

        // Renders whole PackageView
        return Backbone.View.extend({

            el: '#content',

            events: {
                'click #add': 'addPackage',
                'keypress #name': 'addOnEnter'
            },

            initialize: function() {
                this.tree = new TreeCollection();

            },

            init: function() {
                var self = this;
                this.tree.fetch({success: function() {
                    self.render();
                }});
            },

            render: function() {
                var packs = this.tree.get('packages'),
                    files = this.tree.get('files');

                this.$el.append($('<span>Root: ' + this.tree.get('root').get('name') + ' </span>'));
                this.$el.append($('<input id="name" type="text" size="20">'));
                this.$el.append($('<a id="add" href="#"> Add</a><br>'));

                var ul = $('<ul></ul>');
                packs.each(function(pack) {
                    ul.append(new packageView({model: pack}).render().el);
                });

                this.$el.append(ul);
                this.$el.append($('<br> Files: ' + files.size() + '<br>'));

                ul = $('<ul></ul>');
                files.each(function(file) {
                    ul.append(new fileView({model: file}).render().el);
                });

                this.$el.append(ul);

                return this;
            },

            addOnEnter: function(e) {
                if (e.keyCode != 13) return;
                this.addPackage(e);
            },

            addPackage: function() {
                var self = this;
                var settings = {
                    data: {
                        name: '"' + $('#name').val() + '"',
                        links: '["some link"]'
                    },
                    success: function() {
                        self.tree.fetch({success: function() {
                            self.render();
                        }});
                    }
                };

                $.ajax('api/addPackage', settings);
                $('#name').val('');
            }
        });
    });