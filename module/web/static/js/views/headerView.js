define(['jquery', 'underscore', 'backbone', 'app', 'models/ServerStatus', 'flot'],
    function($, _, Backbone, App, ServerStatus) {
        // Renders the header with all information
        return Backbone.View.extend({

            el: 'header',

            events: {
                'click i.iconf-list': 'toggle_taskList',
                'click .popover .close': 'hide_taskList',
                'click .btn-grabber': 'open_grabber'
            },

            templateStatus: _.compile($('#template-header-status').html()),

            // Will hold the link grabber
            grabber: null,
            notifications: null,
            ws: null,

            // Status model
            status: null,

            initialize: function() {
                this.notifications = this.$('#notification-area').calculateHeight().height(0);

                this.status = new ServerStatus();
                this.listenTo(this.status, 'change', this.render);

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
//                console.log('Render header');

                this.$('.status-block').html(
                    this.templateStatus(this.status.toJSON())
                );
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
                else if (data['@class'] === 'progress')
                    this.onProgressUpdate(data);
                else if (data['@class'] === 'event')
                    this.onEvent(data);
                else
                    console.log('Unknown Async input');

            },

            onProgressUpdate: function(progress) {

            },

            onEvent: function(event) {

            }

        });
    });