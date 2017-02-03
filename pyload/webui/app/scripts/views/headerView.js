define(['jquery', 'underscore', 'backbone', 'app', 'models/StatusInfo',
  'views/progressView', 'views/notificationView', 'helpers/formatsize', 'hbs!tpl/header/layout',
  'hbs!tpl/header/status', 'hbs!tpl/header/progressbar', 'hbs!tpl/header/progressSup', 'hbs!tpl/header/progressSub' , 'flot'],
  function(
    $, _, Backbone, App, StatusInfo, ProgressView, NotificationView, formatsize, template, templateStatus, templateProgress, templateSup, templateSub) {
    'use strict';
    // Renders the header with all information
    return Backbone.Marionette.ItemView.extend({

      modelEvents: {
        'change': 'render'
      },

      events: {
        'click .icon-list': 'toggle_taskList',
        'click .popover .close': 'toggle_taskList',
        'click .btn-grabber': 'open_grabber',
        'click .logo': 'gotoDashboard'
      },

      ui: {
        progress: '.progress-list',
        speedgraph: '#speedgraph'
      },

      template: template,

      // view
      grabber: null,
      speedgraph: null,

      // models and data
      ws: null,
      status: null,
      speeds: null,

      // sub view
      notificationView: null,

      // save if last progress was empty
      wasEmpty: false,
      lastStatus: null,

      initialize: function() {
        var self = this;
        this.notificationView = new NotificationView();

        this.model = App.user;

        this.status = new StatusInfo();
        this.listenTo(this.status, 'change', this.update);

        this.listenTo(App.progressList, 'add', function(model) {
          self.ui.progress.appendWithAnimation(new ProgressView({model: model}).render().el);
        });

        // Listen to open the link grabber
        this.listenTo(App.vent, 'linkgrabber:open', function(pack) {
          self.open_grabber(null, pack);
        });

        // TODO: button to start stop refresh
        // TODO: catch ws errors / switch into ws less mode
        try {
          var ws = App.openWebSocket('/async');
          ws.onopen = function() {
            ws.send(JSON.stringify('start'));
          };
          // TODO compare with polling
          ws.onmessage = _.bind(this.onData, this);
          ws.onerror = function(error) {
            console.log(error);
            alert('WebSocket error ' + error);
          };
          ws.onclose = function() {
            alert('WebSocket was closed');
          };

          this.ws = ws;

        } catch (e) {
          alert('Could not open WebSocket: ' + e);
        }
      },

      gotoDashboard: function() {
        App.navigate('');
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
            color: '#fee247'
          },
          xaxis: { ticks: [] },
          yaxis: { ticks: [], min: 1, autoscaleMargin: 0.1, tickFormatter: function(data) {
            return formatsize(data * 1024);
          }, position: 'right' },
          grid: {
            show: true,
//      borderColor: "#757575",
            borderColor: 'white',
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
          templateStatus(status)
        );

        var data = {tasks: 0, downloads: 0, speed: 0, single: false};
        App.progressList.each(function(progress) {
          if (progress.isDownload()) {
            data.downloads++;
            data.speed += progress.get('connection').speed;
          } else
            data.tasks++;
        });

        // Show progress of one task
        if (data.tasks + data.downloads === 1) {
          var progress = App.progressList.at(0);
          data.single = true;
          data.eta = progress.get('eta');
          data.percent = progress.getPercent();
          data.name = progress.get('name');
          data.statusmsg = progress.get('statusmsg');
        }

        data.etaqueue = status.eta;
        data.linksqueue = status.linksqueue;
        data.sizequeue = status.sizequeue;

        // Render progressbar only when needed
        if (!_.isEqual([data.tasks, data.downloads], this.lastStatus)) {
          this.lastStatus = [data.tasks, data.downloads];
          this.$('#progress-info').html(templateProgress(data));
        } else {
          this.$('#progress-info .bar').width(data.percent + '%');
        }

        // render upper and lower part
        this.$('.sup').html(templateSup(data));
        this.$('.sub').html(templateSub(data));

        return this;
      },

      toggle_taskList: function() {
        this.$('.popover').animate({opacity: 'toggle'});
      },

      open_grabber: function(e, model) {
        var self = this;
        _.requireOnce(['views/linkgrabber/modalView'], function(ModalView) {
          if (self.grabber === null)
            self.grabber = new ModalView();

          self.grabber.setModel(model);
          self.grabber.show();
        });
      },

      onData: function(evt) {
        var data = JSON.parse(evt.data);
        if (data === null) return;

        if (data['@class'] === 'StatusInfo') {
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

        App.progressList.set(progress);
        // update currently open files with progress
        App.progressList.each(function(prog) {
          if (prog.isDownload() && App.dashboard.files) {
            var file = App.dashboard.files.get(prog.get('connection').fid);
            if (file) {
              file.setDownloadStatus(prog.get('connection').status);
              file.trigger('change:progress', prog);
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
