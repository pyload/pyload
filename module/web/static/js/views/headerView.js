define(['jquery', 'underscore', 'backbone', 'app', 'models/ServerStatus', 'collections/ProgressList', 'views/progressView', 'flot'],
    function($, _, Backbone, App, ServerStatus, ProgressList, ProgressView) {
        // Renders the header with all information
        return Backbone.View.extend({

            el: 'header',

            events: {
                'click .iconf-list': 'toggle_taskList',
                'click .popover .close': 'hide_taskList',
                'click .btn-grabber': 'open_grabber'
            },

            // todo: maybe combine these
            templateStatus: _.compile($('#template-header-status').html()),
            templateHeader: _.compile($('#template-header').html()),

            // Will hold the link grabber
            grabber: null,
            notifications: null,
            header: null,
            progress: null,
            ws: null,

            // Status model
            status: null,
            progressList: null,

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

                this.ws = ws;

                this.initGraph();
            },

            initGraph: function() {
                var totalPoints = 100;
                var data = [];

                function getRandomData() {
                    if (data.length > 0)
                        data = data.slice(1);

                    // do a random walk
                    while (data.length < totalPoints) {
                        var prev = data.length > 0 ? data[data.length - 1] : 50;
                        var y = prev + Math.random() * 10 - 5;
                        if (y < 0)
                            y = 0;
                        if (y > 100)
                            y = 100;
                        data.push(y);
                    }

                    // zip the generated y values with the x values
                    var res = [];
                    for (var i = 0; i < data.length; ++i)
                        res.push([i, data[i]])
                    return res;
                }

                var updateInterval = 1500;

                var speedgraph = $.plot(this.$el.find("#speedgraph"), [getRandomData()], {
                    series: {
                        lines: { show: true, lineWidth: 2 },
                        shadowSize: 0,
                        color: "#fee247"
                    },
                    xaxis: { ticks: [], mode: "time" },
                    yaxis: { ticks: [], min: 0, autoscaleMargin: 0.1 },
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

                function update() {
                    speedgraph.setData([ getRandomData() ]);
                    // since the axes don't change, we don't need to call plot.setupGrid()
                    speedgraph.draw();

                    setTimeout(update, updateInterval);
                }

//            update();

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

            hide_taskList: function() {
                this.$('.popover').fadeOut();
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
                    if(prog.isDownload() && App.dashboard.files){
                        var file = App.dashboard.files.get(prog.get('download').fid);
                        if (file)
                            file.set('progress', prog.getPercent());
                    }
                });
                // TODO: only render when changed
                this.render();
            },

            onEvent: function(event, args) {
                args.unshift(event);
                console.log('Core send event', args);
                App.vent.trigger.apply(App.vent, args);
            }

        });
    });