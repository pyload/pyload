define(['jquery', 'backbone', 'underscore', 'app', 'utils/apitypes', 'views/abstract/itemView', 'helpers/formatTimeLeft', 'hbs!tpl/dashboard/file'],
    function($, Backbone, _, App, Api, ItemView, formatTime, template) {
        'use strict';

        // Renders single file item
        return ItemView.extend({

            tagName: 'li',
            className: 'file-view row-fluid',
            template: template,
            events: {
                'click .checkbox': 'select',
                'click .btn-delete': 'deleteItem',
                'click .btn-restart': 'restart'
            },

            initialize: function() {
                this.listenTo(this.model, 'change', this.render);
                // This will be triggered manually and changed before with silent=true
                this.listenTo(this.model, 'change:visible', this.visibility_changed);
                this.listenTo(this.model, 'change:progress', this.onProgressChanged);
                this.listenTo(this.model, 'remove', this.unrender);
                this.listenTo(App.vent, 'dashboard:destroyContent', this.destroy);
            },

            onDestroy: function() {
            },

            render: function() {
                var data = this.model.toJSON();
                if (data.download) {
                    var status = data.download.status;
                    if (status === Api.DownloadStatus.Offline || status === Api.DownloadStatus.TempOffline)
                        data.offline = true;
                    else if (status === Api.DownloadStatus.Online)
                        data.online = true;
                    else if (status === Api.DownloadStatus.Waiting)
                        data.waiting = true;
                    else if (status === Api.DownloadStatus.Downloading)
                        data.downloading = true;
                    else if (this.model.isFailed())
                        data.failed = true;
                    else if (this.model.isFinished())
                        data.finished = true;
                }

                this.$el.html(this.template(data));
                if (this.model.get('selected'))
                    this.$el.addClass('ui-selected');
                else
                    this.$el.removeClass('ui-selected');

                if (this.model.get('visible'))
                    this.$el.show();
                else
                    this.$el.hide();

                return this;
            },

            select: function(e) {
                e.preventDefault();
                var checked = this.$el.hasClass('ui-selected');
                // toggle class immediately, so no re-render needed
                this.model.set('selected', !checked, {silent: true});
                this.$el.toggleClass('ui-selected');
                App.vent.trigger('file:selection');
            },

            visibility_changed: function(visible) {
                // TODO: improve animation, height is not available when element was not visible
                if (visible)
                    this.$el.slideOut(true);
                else {
                    this.$el.calculateHeight(true);
                    this.$el.slideIn(true);
                }
            },

            onProgressChanged: function(prog) {
                // TODO: progress for non download statuses
                if (!this.model.isDownload())
                    return;

                // criteria for re-rendering
                // ensure that the dl bar is rendered
                var render = !this.$('.progress .bar') || this.model.get('size') !== prog.get('total');

                this.model.set({
                    progress: prog.getPercent(),
                    eta: prog.get('eta'),
                    size: prog.get('total')
                }, {silent: true});

                if (this.model.get('download').status === Api.DownloadStatus.Downloading) {
                    if (render)
                        this.render();

                    var bar = this.$('.progress .bar');

                    bar.width(this.model.get('progress') + '%');
                    bar.html('&nbsp;&nbsp;' + formatTime(this.model.get('eta')));
                } else if (this.model.get('download').status === Api.DownloadStatus.Waiting) {
                    this.$('.second').html(
                        '<i class="icon-time"></i>&nbsp;' + formatTime(this.model.get('eta')));

                } else // Every else state can be rendered normally
                    this.render();

            }
        });
    });
