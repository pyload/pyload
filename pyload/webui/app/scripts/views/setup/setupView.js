define(['jquery', 'backbone', 'underscore', 'app', 'models/Setup', 'hbs!tpl/setup/layout', 'hbs!tpl/setup/actionbar', 'hbs!tpl/setup/error',
    './welcomeView', './systemView', './userView', './finishedView'],
    function($, Backbone, _, App, Setup, template, templateBar, templateError, welcomeView, systemView, userView, finishedView) {
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
                systemView,
                userView,
                finishedView
            ],

            page: 0,
            view: null,
            error: null,

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
                    self.openPage(self.page + 1);
                });
                this.listenTo(this.model, 'page:prev', function() {
                    self.openPage(self.page - 1);
                });

                this.listenTo(this.model, 'error', this.onError);
                this.model.fetch();
            },

            openPage: function(page) {
                console.log('Change page', page);
                // check if number is reasonable
                if (!_.isNumber(page) || !_.isFinite(page) || page < 0 || page >= this.pages.length)
                    return;

                if (page === this.page)
                    return;

                // Render error directly
                if (this.error) {
                    this.onRender();
                    return;
                }

                this.page = page;

                var self = this;
                this.ui.page.fadeOut({complete: function() {
                    self.onRender();
                }});

                this.model.trigger('page:changed', page);
            },

            onError: function(model, xhr) {
                console.log('Setup error', xhr);
                this.error = xhr;
                this.onRender();
            },

            onRender: function() {

                // close old opened view
                if (this.view)
                    this.view.close();

                // Render error if occurred
                if (this.error) {
                    this.ui.page.html(templateError(this.error));
                    return;
                }

                this.view = new this.pages[this.page]({model: this.model});
                this.ui.page.empty();

                var el = this.view.render().el;
                this.ui.page.append(el);

                this.ui.page.fadeIn();
            }

        });
    });
