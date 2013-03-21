define(['jquery', 'underscore', 'backbone', 'app', 'models/ServerStatus', 'collections/ProgressList',
    'views/progressView', 'helpers/formatSize', 'flot'],
    function($, _, Backbone, App, ServerStatus, ProgressList, ProgressView, formatSize) {
        // Renders the header with all information
        return Backbone.View.extend({

            el: 'header',

            events: {
                'click .iconf-list': 'toggle_taskList',
                'click .popover .close': 'toggle_taskList',
                'click .btn-grabber': 'open_grabber'
            },

            // todo: maybe combine these
            templateStatus: _.compile($('#template-header-status').html()),
            templateHeader: _.compile($('#template-header').html()),

            // html elements
            grabber: null,
            notifications: null,
            header: null,
            progress: null,
            speedgraph: null,

            // models and data
            ws: null,
            status: null,
            progressList: null,
            speeds: null,

            // save if last progress was empty
            wasEmpty: false,

            initialize: function() {
                var self = this;
                this.notifications = this.$('#notification-area').calculateHeight().height(0);

                this.status = new ServerStatus();
                this.listenTo(this.status, 'change', this.render);

                this.progress = this.$('.progress-list');
                this.progressList = new ProgressList();
                this.listenTo(this.progressList, 'add', function(model) {
                    self.progress.appendWithAnimation(new ProgressView({model: model}).render().el);
                });

                // TODO: button to start stop refresh
                var ws = App.openWebSocket('/async');
                ws.onopen = function() {
                    ws.send(JSON.stringify('start'));
                };
                // TODO compare with polling
                ws.onmessage = _.bind(this.onData, this);
                ws.onerror = function(error) {
                    alert(error);
                };

                this.ws = ws;

                this.initGraph();
            },

            initGraph: function() {
                var totalPoints = 120;
                var data = [];

                // init with empty data
                while (data.length < totalPoints)
                    data.push([data.length, 0]);

                this.speeds = data;
                this.speedgraph = $.plot(this.$el.find("#speedgraph"), [this.speeds], {
                    series: {
                        lines: { show: true, lineWidth: 2 },
                        shadowSize: 0,
                        color: "#fee247"
                    },
                    xaxis: { ticks: [], mode: "time" },
                    yaxis: { ticks: [], min: 1, autoscaleMargin: 0.1, tickFormatter: function(data) {
                        return formatSize(data * 1024);
                    }, position: "right" },
                    grid: {
                        show: true,
//            borderColor: "#757575",
                        borderColor: "white",
                        borderWidth: 1,
                        labelMargin: 0,
                        axisMargin: 0,
                        minBorderMargin: 0
                    }
                });

            },

            render: function() {
                // TODO: what should be displayed in the header
                // queue/processing size?

                this.$('.status-block').html(
                    this.templateStatus(this.status.toJSON())
                );

                var data = {tasks: 0, downloads: 0, speed: 0};
                this.progressList.each(function(progress) {
                    if (progress.isDownload()) {
                        data.downloads += 1;
                        data.speed += progress.get('download').speed;
                    } else
                        data.tasks++;
                });

                this.$('#progress-info').html(
                    this.templateHeader(data)
                );
                return this;
            },

            toggle_taskList: function() {
                this.$('.popover').animate({opacity: 'toggle'});
            },

            open_grabber: function() {
                var self = this;
                _.requireOnce(['views/linkGrabberModal'], function(modalView) {
                    if (self.grabber === null)
                        self.grabber = new modalView();

                    self.grabber.show();
                });
            },

            onData: function(evt) {
                var data = JSON.parse(evt.data);
                if (data === null) return;

                if (data['@class'] === "ServerStatus") {
                    this.status.set(data);

                    this.speeds = this.speeds.slice(1);
                    this.speeds.push([this.speeds[this.speeds.length - 1][0] + 1, Math.floor(data.speed / 1024)]);

                    // TODO: if everything is 0 rerender is not needed
                    this.speedgraph.setData([this.speeds]);
                    // adjust the axis
                    this.speedgraph.setupGrid();
                    this.speedgraph.draw();

                }
                else if (_.isArray(data))
                    this.onProgressUpdate(data);
                else if (data['@class'] === 'EventInfo')
                    this.onEvent(data.eventname, data.event_args);
                else
                    console.log('Unknown Async input');

            },

            onProgressUpdate: function(progress) {
                // generate a unique id
                _.each(progress, function(prog) {
                    if (prog.download)
                        prog.pid = prog.download.fid;
                    else
                        prog.pid = prog.plugin + prog.name;
                });

                this.progressList.update(progress);
                // update currently open files with progress
                this.progressList.each(function(prog) {
                    if (prog.isDownload() && App.dashboard.files) {
                        var file = App.dashboard.files.get(prog.get('download').fid);
                        if (file) {
                            file.set({
                                progress: prog.getPercent(),
                                eta: prog.get('eta'),
                            }, {silent: true});

                            file.trigger('change:progress');
                        }
                    }
                });

                if (progress.length === 0) {
                    // only render one time when last was not empty already
                    if (!this.wasEmpty) {
                        this.render();
                        this.wasEmpty = true;
                    }
                } else {
                    this.wasEmpty = false;
                    this.render();
                }
            },

            onEvent: function(event, args) {
                args.unshift(event);
                console.log('Core send event', args);
                App.vent.trigger.apply(App.vent, args);
            }

        });
    });