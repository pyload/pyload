define(['jquery', 'backbone', 'underscore', 'models/TreeCollection', 'views/packageView', 'views/fileView'],
    function($, Backbone, _, TreeCollection, packageView, fileView) {

        // Renders whole PackageView
        return Backbone.View.extend({

            el: '#content',

            events: {
                'click #add': 'addPackage',
                'keypress #name': 'addOnEnter',
                'click #show_active': 'filter'
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
                    files = this.tree.get('files'),
                    el = this.$('#dashboard');

                el.empty();
                el.append($('<span>Root: ' + this.tree.get('root').get('name') + ' </span>'));
                el.append($('<input id="name" type="text" size="20">'));
                el.append($('<a id="add" href="#"> Add</a><br>'));

                var ul = $('<ul></ul>');
                packs.each(function(pack) {
                    ul.append(new packageView({model: pack}).render().el);
                });

                el.append(ul);
                el.append($('<br> Files: ' + files.size() + '<br>'));

                ul = $('<ul></ul>');
                files.each(function(file) {
                    ul.append(new fileView({model: file}).render().el);
                });

                el.append(ul);
                $('#name').focus();

                return this;
            },

            addOnEnter: function(e) {
                if (e.keyCode != 13) return;
                this.addPackage(e);
            },

            addPackage: function(e) {
                var self = this;
                var settings = {
                    type: 'POST',
                    data: {
                        name: JSON.stringify($('#name').val()),
                        links: JSON.stringify(['http://download.pyload.org/random.bin', 'invalid link'])
                    },
                    success: function() {
                        self.tree.fetch({success: function() {
                            self.render();
                        }});
                    }
                };

                $.ajax('api/addPackage', settings);
                $('#name').val('');
            },

            toggle: false,

            filter: function(e) {
                var self = this;
                this.tree.get('packages').each(function(item){
                    if(!self.toggle)
                       item.trigger('filter:added');
                    else
                        item.trigger('filter:removed');

                });
                self.toggle ^= true;
            }
        });
    });