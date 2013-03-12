define(['jquery', 'underscore', 'app', 'views/abstract/modalView', 'text!tpl/default/linkgrabber.html'],
    function($, _, App, modalView, template) {
        // Modal dialog for package adding - triggers package:added when package was added
        return modalView.extend({

            events: {
                'click .btn-success': 'addPackage',
                'keypress #inputPackageName': 'addOnEnter'
            },

            template: _.compile(template),

            initialize: function() {
                // Inherit parent events
                this.events = _.extend({}, modalView.prototype.events, this.events);
            },

            renderContent: function() {
                return $('<h1>Content!</h1>');
            },

            addOnEnter: function(e) {
                if (e.keyCode != 13) return;
                this.addPackage(e);
            },

            addPackage: function(e) {
                var self = this;
                var settings = {
                    type: 'POST',
                    data: {
                        name: JSON.stringify($('#inputPackageName').val()),
                        links: JSON.stringify(['http://download.pyload.org/random.bin', 'http://download.pyload.org/random100.bin',
                            'invalid link', 'invalid link 2', 'invalid link 3', 'inavlid link 4',
                            'http://download.pyload.org/random.bin', 'http://download.pyload.org/random.bin', 'http://download.pyload.org/random.bin',
                            'A really really long invalid url that should exceed length of most of the urls by far and split into two lines'])
                    },
                    success: function() {
                        App.vent.trigger('package:added');
                        self.hide();
                    }
                };

                $.ajax('api/addPackage', settings);
                $('#inputPackageName').val('');
            },

            onShow: function() {
                this.$('#inputPackageName').focus();
            }

        });
    });