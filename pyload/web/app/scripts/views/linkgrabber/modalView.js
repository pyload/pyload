define(['jquery', 'underscore', 'backbone', 'app', 'models/CollectorPackage', 'views/abstract/modalView', './collectorView', 'hbs!tpl/linkgrabber/modal'],
    function($, _, Backbone, App, CollectorPackage, modalView, CollectorView, template) {
        'use strict';
        // Modal dialog for package adding - triggers package:added when package was added
        return modalView.extend({

            className: 'modal linkgrabber',
            events: {
                'keyup #inputLinks': 'addOnKeyUp',
                'click .btn-container': 'selectContainer',
                'change #inputContainer': 'checkContainer',
                'keyup #inputURL': 'checkURL',
                'click .btn-remove-all': 'clearAll'
            },

            template: template,

            // Holds the view that display the packages
            collectorView: null,

            inputSize: 0,

            initialize: function() {
                // Inherit parent events
                this.events = _.extend({}, modalView.prototype.events, this.events);
                this.listenTo(App.vent, 'package:added', _.bind(this.onAdded, this));
            },

            addOnKeyUp: function(e) {
                // Enter adds the links
                if (e.keyCode === 13)
                    this.checkLinks();

                var inputSize = this.$('#inputLinks').val().length;

                // TODO: checkbox to disable this
                // add links when several characters was pasted into box
                if (inputSize > this.inputSize + 4)
                    this.checkLinks();
                else
                    this.inputSize = inputSize;
            },

            checkLinks: function() {
                var self = this;
                // split, trim and remove empty links
                var links = _.filter(_.map(this.$('#inputLinks').val().split('\n'), function(link) {
                    return $.trim(link);
                }), function(link) {
                    return link.length > 0;
                });

                var options = App.apiRequest('checkLinks',
                    {links: links},
                    {
                        success: function(data) {
                            self.collectorView.updateData(data);
                        }
                    });

                $.ajax(options);
                this.$('#inputLinks').val('');
                this.inputSize = 0;
            },

            selectContainer: function(e) {
                this.$('#inputContainer').trigger('click');
            },

            checkContainer: function(e) {
                this.$('form').attr('action', App.apiUrl('api/checkContainer'));
                this.$('form').trigger('submit');
            },

            checkURL: function(e) {
                // check is triggered on enter
                if (e.keyCode !== 13)
                    return;

                var self = this;
                $.ajax(App.apiRequest('checkHTML', {
                    html: '',
                    url: $(e.target).val()
                }, {
                    success: function(data) {
                        self.collectorView.updateData(data);
                    }
                }));

                $(e.target).val('');
            },

            // deletes every package
            clearAll: function(e) {
                this.collectorView.collection.reset();

            },

            // Hide when there are no more packages
            onAdded: function() {
                if (this.collectorView !== null) {
                    if (this.collectorView.collection.length === 0)
                        this.hide();
                }
            },

            onRender: function() {
                // anonymous collection
                this.collectorView = new CollectorView({collection: new (Backbone.Collection.extend({
                    model: CollectorPackage
                }))()});
                this.collectorView.setElement(this.$('.prepared-packages'));
            },

            onDestroy: function() {
                if (this.collectorView)
                    this.collectorView.close();
            }

        });
    });