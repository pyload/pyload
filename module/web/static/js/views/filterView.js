define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes'],
    function($, Backbone, _, App, Api) {

        // Renders the actionbar for the dashboard, handles everything related to filtering displayed files
        return Backbone.View.extend({
            el: 'ul.actionbar',

            events: {
                'click .filter-type': 'filter_type',
                'click .filter-state': 'switch_filter'
            },

            state: null,
            stateMenu: null,

            initialize: function() {
                this.$('.search-query').typeahead({
                    minLength: 2,
                    source: this.getAutocompletion
                });

                this.stateMenu = this.$('.dropdown-toggle .state');
                this.state = Api.DownloadState.All;
            },

            render: function() {
                return this;
            },

            getAutocompletion: function() {
                return ["static", "autocompletion", "demo", "with", "some", "keywords",
                    "a very long proposal for autocompletion"];
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