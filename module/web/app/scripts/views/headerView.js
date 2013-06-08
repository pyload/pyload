define(['jquery', 'underscore', 'backbone', 'app', 'models/ServerStatus', 'collections/ProgressList',
    'views/progressView', 'views/notificationView', 'helpers/formatSize', 'hbs!tpl/header/layout',
    'hbs!tpl/header/status', 'hbs!tpl/header/progressbar' , 'flot'],
    function($, _, Backbone, App, ServerStatus, ProgressList, ProgressView, notificationView, formatSize,
             template, templateStatus, templateHeader) {
        'use strict';
        // Renders the header with all information
        return Backbone.Marionette.ItemView.extend({

            events: {
                'click .icon-list': 'toggle_taskList',
                'click .popover .close': 'toggle_taskList',
                'click .btn-grabber': 'open_grabber'
            },

            ui: {
                progress: '.progress-list',
                speedgraph: '#speedgraph'
            },

            // todo: maybe combine these
            template: template,
            templateStatus: templateStatus,
            templateHeader: templateHeader,

            // view
            grabber: null,
            speedgraph: null,

            // models and data
            ws: null,
            status: null,
            progressList: null,
            speeds: null,

            // sub view
            notificationView: null,

            // save if last progress was empty
            wasEmpty: false,

            initialize: function() {
                var self = this;
                this.notificationView = new notificationView();

                this.status = new ServerStatus();
                this.listenTo(this.status, 'change', this.update);

                this.progressList = new ProgressList();
                this.listenTo(this.progressList, 'add', function(model) {
                    self.ui.progress.appendWithAnimation(new ProgressView({model: model}).render().el);
                });

                // TODO: button to start stop refresh
                var ws = App.openWebSocket('/async');
                ws.onopen = function() {
                    ws.send(JSON.stringify('start'));
                };
                // TODO compare with polling
                ws.onmessage = _.bind(this.onData, this);
                ws.onerror = function(error) {
                    console.log(error);
                    alert("WebSocket error" + error);
                };

                this.ws = ws;
            },

            initGraph: function() {
                var totalPoints = 120;
                var data = [];

                // init with empty data
                while (data.length < totalPoints)
                    data.push([data.length, 0]);

                this.speeds = data;
                this.speedgraph = $.plot(this.ui.speedgraph, [this.speeds], {
                    series: {
                        lines: { show: true, lineWidth: 2 },
                        shadowSize: 0,
                        color: "#fee247"
                    },
                    xaxis: { ticks: [] },
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

            // Must be called after view was attached
            init: function() {
                this.initGraph();
                this.update();
            },

            update: function() {
                // TODO: what should be displayed in the header
                // queue/processing size?

                var status = this.status.toJSON();
                status.maxspeed = _.max(this.speeds, function(speed) {
                    return speed[1];
                })[1] * 1024;
                this.$('.status-block').html(
                    this.templateStatus(status)
                );

                var data = {tasks: 0, downloads: 0, speed: 0, single: false};
                this.progressList.each(function(progress) {
                    if (progress.isDownload()) {
                        data.downloads += 1;
                        data.speed += progress.get('download').speed;
                    } else
                        data.tasks++;
                });

                // Show progress of one task
                if (data.tasks + data.downloads === 1) {
                    var progress = this.progressList.at(0);
                    data.single = true;
                    data.eta = progress.get('eta');
                    data.percent = progress.getPercent();
                    data.name = progress.get('name');
                    data.statusmsg = progress.get('statusmsg');
                }
                // TODO: better progressbar rendering

                data.etaqueue = status.eta;
                data.linksqueue = status.linksqueue;
                data.sizequeue = status.sizequeue;

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
                    // TODO: load interaction when none available
                    this.status.set(data);

                    // There tasks at the server, but not in queue: so fetch them
                    // or there are tasks in our queue but not on the server
                    if (this.status.get('notifications') && !this.notificationView.tasks.hasTaskWaiting() ||
                        !this.status.get('notifications') && this.notificationView.tasks.hasTaskWaiting())
                        this.notificationView.tasks.fetch();

                    this.speeds = this.speeds.slice(1);
                    this.speeds.push([this.speeds[this.speeds.length - 1][0] + 1, Math.floor(data.speed / 1024)]);

                    // TODO: if everything is 0 re-render is not needed
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
                    console.log('Unknown Async input', data);

            },

            onProgressUpdate: function(progress) {
                // generate a unique id
                _.each(progress, function(prog) {
                    if (prog.download)
                        prog.pid = prog.download.fid;
                    else
                        prog.pid = prog.plugin + prog.name;
                });

                this.progressList.set(progress);
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
                        this.update();
                        this.wasEmpty = true;
                    }
                } else {
                    this.wasEmpty = false;
                    this.update();
                }
            },

            onEvent: function(event, args) {
                args.unshift(event);
                console.log('Core send event', args);
                App.vent.trigger.apply(App.vent, args);
            }

        });
    });