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
            require(['views/settings/settingsView'], function(SettingsView) {
                App.settingsView = new SettingsView();
                App.settingsView.render();
            });
        };

        App.initAccountView = function() {
            require(['views/accounts/accountListView'], function(AccountListView) {
                App.accountView = new AccountListView();
                App.accountView.render();
            });
        };

        return App;
    });