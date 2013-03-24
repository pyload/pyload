define('default', ['require', 'jquery', 'app', 'views/headerView', 'views/dashboard/dashboardView'],
    function(require, $, App, HeaderView, DashboardView) {

        App.init = function() {
            App.header = new HeaderView();
            App.header.render();
        };

        App.initDashboard = function() {
            $(function() {
                App.dashboard = new DashboardView();
                App.dashboard.init();
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