define(['jquery', 'backbone', 'underscore', 'app', 'models/TreeCollection', 'views/packageView', 'views/fileView'],
    function($, Backbone, _, App, TreeCollection, packageView, fileView) {

        // Renders whole PackageView
        return Backbone.View.extend({

            el: '#content',

            events: {
                'click #show_active': 'filter'
            },

            // <ul> holding the packages
            packageUL: null,

            initialize: function() {
                var self = this;
                this.tree = new TreeCollection();

                // When package is added we reload the data
                App.vent.on('package:added', function() {
                    console.log('Package tree caught, package:added event');
                    self.tree.fetch();
                });

            },

            init: function() {
                var self = this;

                // TODO: put in separated function
                // TODO: order of elements?
                // Init the tree and callback for package added
                this.tree.fetch({success: function() {
                    self.render();
                    self.tree.get('packages').on('add', function(pack) {
                        console.log('Package ' + pack.get('pid') + ' added to tree');
                        self.appendPackage(pack, 0, true);

                    })
                }});
            },

            render: function() {
                var packs = this.tree.get('packages'),
                    files = this.tree.get('files'),
                    el = this.$('#dashboard');

                el.empty();

                this.packageUL = $('<ul></ul>');
                packs.each(_.bind(this.appendPackage, this));

                el.append(this.packageUL);
                el.append($('<br> Files: ' + files.size() + '<br>'));

                var ul = $('<ul></ul>');
                files.each(function(file) {
                    ul.append(new fileView({model: file}).render().el);
                });

                el.append(ul);

                return this;
            },

            // TODO sorting ?!
            // Append a package to the list, index, animate it
            appendPackage: function(pack, i, animation) {
                var el = new packageView({model: pack}).render().el;
                if (animation == true)
                    $(el).hide();

                this.packageUL.append(el);

                if (animation == true)
                    $(el).fadeIn();
            },


            // TODO: remove this debug stuff
            toggle: false,

            filter: function(e) {
                var self = this;
                this.tree.get('packages').each(function(item) {
                    if (!self.toggle)
                        item.trigger('filter:added');
                    else
                        item.trigger('filter:removed');

                });
                self.toggle ^= true;
            }
        });
    });