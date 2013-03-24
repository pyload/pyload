define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'models/Package'],
    function($, Backbone, _, App, Api, Package) {

        // Modified version of type ahead show, nearly the same without absolute positioning
        function show() {
            this.$menu
                .insertAfter(this.$element)
                .show();

            this.shown = true;
            return this;
        }

        // Renders the actionbar for the dashboard, handles everything related to filtering displayed files
        return Backbone.View.extend({
            el: 'ul.actionbar',

            events: {
                'click .filter-type': 'filter_type',
                'click .filter-state': 'switch_filter',
                'submit .form-search': 'search'
            },

            state: null,
            stateMenu: null,

            initialize: function() {

                // use our modified method
                $.fn.typeahead.Constructor.prototype.show = show;
                this.$('.search-query').typeahead({
                    minLength: 2,
                    source: this.getSuggestions
                });

                this.stateMenu = this.$('.dropdown-toggle .state');
                this.state = Api.DownloadState.All;

                // Apply the filter before the content is shown
                App.vent.on('dashboard:contentReady', _.bind(this.apply_filter, this));
            },

            render: function() {
                return this;
            },

            // TODO: app level api request

            search: function(e) {
                e.stopPropagation();
                var input = this.$('.search-query');
                var query = input.val();
                input.val('');

                var pack = new Package();
                // Overwrite fetch method to use a search
                // TODO: quite hackish, could be improved to filter packages
                //       or show performed search
                pack.fetch = function(options) {
                    pack.search(query, options);
                };

                App.dashboard.openPackage(pack);
            },

            getSuggestions: function(query, callback) {
                $.ajax('/api/searchSuggestions', {
                    method: 'POST',
                    data: {pattern: JSON.stringify(query)},
                    success: function(data) {
                        callback(data);
                    }
                });
            },

            switch_filter: function(e) {
                e.stopPropagation();
                var element = $(e.target);
                var state = parseInt(element.data('state'), 10);
                var menu = this.stateMenu.parent().parent();
                menu.removeClass('open');

                if (state === Api.DownloadState.Finished) {
                    menu.removeClass().addClass('dropdown finished');
                } else if (state === Api.DownloadState.Unfinished) {
                    menu.removeClass().addClass('dropdown active');
                } else if (state === Api.DownloadState.Failed) {
                    menu.removeClass().addClass('dropdown failed');
                } else {
                    menu.removeClass().addClass('dropdown');
                }

                this.state = state;
                this.stateMenu.text(element.text());
                this.apply_filter();
            },

            // Applies the filtering to current open files
            apply_filter: function() {
                if (!App.dashboard.files)
                    return;

                var self = this;
                App.dashboard.files.map(function(file) {
                    var visible = file.get('visible');
                    if (visible !== self.is_visible(file)) {
                        file.set('visible', !visible, {silent: true});
                        file.trigger('change:visible', !visible);
                    }
                });

                App.vent.trigger('dashboard:filtered');
            },

            // determine if a file should be visible
            // TODO: non download files
            is_visible: function(file) {
                if (this.state === Api.DownloadState.Finished)
                    return file.isFinished();
                else if (this.state === Api.DownloadState.Unfinished)
                    return file.isUnfinished();
                else if (this.state === Api.DownloadState.Failed)
                    return file.isFailed();

                return true;
            },

            filter_type: function(e) {

            }

        });
    });