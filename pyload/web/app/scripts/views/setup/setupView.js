define(['jquery', 'backbone', 'underscore', 'app', 'models/Setup', 'hbs!tpl/setup/layout', 'hbs!tpl/setup/actionbar',
    './welcomeView', './systemView'],
    function($, Backbone, _, App, Setup, template, templateBar, welcomeView, systemView) {
        'use strict';

        return Backbone.Marionette.ItemView.extend({
            template: template,

            events: {
            },

            ui: {
                page: '.setup-page'
            },

            pages: [
                welcomeView,
                systemView
            ],

            page: 0,
            view: null,

            initialize: function() {
                var self = this;
                this.model = new Setup();

                this.actionbar = Backbone.Marionette.ItemView.extend({
                    template: templateBar,
                    view: this,
                    events: {
                        'click .select-page': 'selectPage'
                    },

                    initialize: function() {
                        this.listenTo(self.model, 'page:changed', this.render);
                    },

                    serializeData: function() {
                        return {
                            page: this.view.page,
                            max: this.view.pages.length - 1,
                            pages: _.map(this.view.pages, function(p) {
                                return p.prototype.name;
                            })
                        };
                    },

                    selectPage: function(e) {
                        this.view.openPage(parseInt($(e.target).data('page'), 10));
                    }

                });
                this.listenTo(this.model, 'page:next', function() {
                    self.openPage(self.page++);
                });
                this.listenTo(this.model, 'page:prev', function() {
                    self.openPage(self.page--);
                });
            },

            openPage: function(page) {
                console.log('Change page', page);
                // check if number is reasonable
                if (!_.isNumber(page) || !_.isFinite(page))
                    return;

                if (page === this.page)
                    return;

                this.page = page;
                this.onRender();

                this.model.trigger('page:changed', page);
            },

            onRender: function() {
                // close old opened view
                if (this.view)
                    this.view.close();

                // TODO: animation
                this.view = new this.pages[this.page]({model: this.model});
                this.ui.page.empty();
                this.ui.page.append(this.view.render().$el);
            }

        });
    });