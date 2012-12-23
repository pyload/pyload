define('default', ['jquery', 'app', 'views/headerView', 'views/packageTreeView'],
    function($, App, HeaderView, TreeView) {

        App.init = function() {
            var view = new HeaderView();
            view.render();
        };

        App.initPackageTree = function() {
            $(function() {
                var view = new TreeView();
                view.init();
            });
        };

        return App;
    });