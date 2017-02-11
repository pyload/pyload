define(['jquery', 'backbone', 'underscore', 'app', 'models/account'], function($, Backbone, _, App, Account) {
  'use strict';

  return Backbone.Collection.extend({

    model: Account,

    comparator: function(account) {
      return account.get('plugin');
    },

    initialize: function() {

    },

    fetch: function(options) {
      options = App.apiRequest('getAccounts', null, options);
      return Backbone.Collection.prototype.fetch.call(this, options);
    }

  });

});
