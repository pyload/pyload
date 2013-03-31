define(['jquery', 'underscore', 'backbone', 'app', 'collections/AccountList', './accountView'],
    function($, _, Backbone, App, AccountList, accountView) {

        // Renders settings over view page
        return Backbone.View.extend({

            el: "body",

            events: {
                'click .btn-add': 'addAccount'
            },

            content: null,
            accounts: null,
            modal: null,

            initialize: function() {
                this.content = this.$('#account-content');
                this.accounts = new AccountList();
                this.refresh();
            },

            refresh: function() {
                this.accounts.fetch({success: _.bind(this.render, this)});
            },

            render: function() {
                var self = this;
                this.accounts.each(function(account) {
                    self.content.append(new accountView({model: account}).render().el);
                });
            },

            addAccount: function() {
                var self = this;
                _.requireOnce(['views/accounts/accountModal'], function(Modal) {
                    if (self.modal === null)
                        self.modal = new Modal();

                    self.modal.show();
                });
            }
        });
    });