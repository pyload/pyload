define([
  'app',
  'backbone',
  'jquery',
  'underscore',

  // Views
  'views/headerview',
  'hbs!tpl/header/blank',
  'views/notificationview',
  'views/dashboard/dashboardview',
  'views/dashboard/selectionview',
  'views/dashboard/filterview',
  'views/loginview',
  'views/settings/settingsview',
  'views/accounts/accountlistview'
], function(
  App, Backbone, $, _, HeaderView, blankHeader, NotificationView, DashboardView, SelectionView, FilterView, LoginView, SettingsView, AccountListView) {
  'use strict';
  return {

    // resets the main views
    reset: function() {
      if (App.header.currentView) {
        App.header.currentView.close();
        App.header.$el.html(blankHeader());
        App.header.currentView = null;
      }
      if (App.content.currentView) {
        App.content.currentView.close();
      }

      if (App.actionbar.currentView) {
        App.actionbar.currentView.close();
      }
    },

    header: function() {
      if (!App.header.currentView) {
        App.header.show(new HeaderView());
        App.header.currentView.init();
      }
      if (!App.notification.currentView) {
        App.notification.attachView(new NotificationView());
      }
    },

    dashboard: function() {
      this.header();

      App.actionbar.show(new FilterView());

      // now visible every time
      if (_.isUndefined(App.selection.currentView) || _.isNull(App.selection.currentView))
        App.selection.attachView(new SelectionView());

      App.content.show(new DashboardView());
    },

    login: function() {
      this.reset();

      App.content.show(new LoginView());
    },

    logout: function() {
      this.reset();

      $.ajax(App.apiRequest('logout', null, {
          success: function() {
            App.user.destroy();
            App.navigate('login');
          }
        }
      ));
    },

    settings: function() {
      this.header();

      var view = new SettingsView();
      App.actionbar.show(new view.actionbar());
      App.content.show(view);
    },

    accounts: function() {
      this.header();

      var view = new AccountListView();
      App.actionbar.show(new view.actionbar());
      App.content.show(view);
    },

    admin: function() {
      alert('Not implemented');
    }
  };

});
