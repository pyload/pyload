define(['jquery', 'underscore', 'backbone', 'app', 'collections/AccountList', './accountView',
    'hbs!tpl/accounts/layout', 'hbs!tpl/accounts/actionbar'],
    function($, _, Backbone, App, AccountList, accountView, template, templateBar) {
        'use strict';

        // Renders settings over view page
        return Backbone.Marionette.CollectionView.extend({

            itemView: accountView,
            template: template,

            collection: null,
            modal: null,

            initialize: function() {
                this.actionbar = Backbone.Marionette.ItemView.extend({
                    template: templateBar,
                    events: {
                        'click .btn': 'addAccount'
                    },
                    addAccount: _.bind(this.addAccount, this)
                });

                this.collection = new AccountList();
                this.update();

                this.listenTo(App.vent, 'account:updated', this.update);
            },

            update: function() {
                this.collection.fetch();
            },

            onBeforeRender: function() {
                this.$el.html(template());
            },

            appendHtml: function(collectionView, itemView, index) {
                this.$('.account-list').append(itemView.el);
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
