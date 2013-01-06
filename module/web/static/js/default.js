define('default', ['require', 'jquery', 'app', 'views/headerView', 'views/packageTreeView'],
    function(require, $, App, HeaderView, TreeView) {

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

        App.initSettingsView = function() {
            require(['views/settingsView'], function(SettingsView) {
                App.settingsView = new SettingsView();
                App.settingsView.render();
            });
        };

        return App;
    });