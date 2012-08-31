define(['jquery', 'backbone', 'underscore', 'models/TreeCollection'], function($, Backbone, _, TreeCollection){

    // Renders whole PackageView
    return Backbone.View.extend({

        el: '#content',

        events: {

        },

        initialize: function() {
            _.bindAll(this, 'render');

            this.tree = new TreeCollection();

        },

        init: function() {
            var self = this;
            this.tree.fetch({success: function(){
                self.render();
            }});
        },


        render: function() {

            var packs = this.tree.get('packages'),
                files = this.tree.get('files'),
                html = 'Root: ' +  this.tree.get('root').get('name') + '<br>';

            html += 'Packages: ' + packs.size();
            html += '<br><ul>';

            packs.each(function(pack){
                html += '<li>'+ pack.get('pid') + pack.get('name') + '</li>';
            });

            html += '</ul><br> Files: ' + files.size() + '<br><ul>';
            files.each(function(file){
                html += '<li>'+ file.get('fid') + file.get('name') + '</li>';
            });

            html += '</ul>';


            this.$el.html(html);

            return this;
        }

    });
});