define('default', ['jquery', 'app', 'views/headerView', 'views/packageTreeView'],
    function($, App, HeaderView, TreeView) {

        App.init = function() {
            App.header = new HeaderView();
            App.header.render();
        };

        App.initPackageTree = function() {
            $(function() {
                App.treeView = new TreeView();
                App.treeView.init();
            });
        };

        return App;
    });