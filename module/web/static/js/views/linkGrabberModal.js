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
                var options = App.apiRequest('addPackage',
                    {
                        name: $('#inputPackageName').val(),
                        // TODO: better parsing / tokenization
                        links: $('#inputLinks').val().split("\n")
                    },
                    {
                        success: function() {
                            App.vent.trigger('package:added');
                            self.hide();
                        }
                    });

                $.ajax(options);
                $('#inputPackageName').val('');
                $('#inputLinks').val('');
            },

            onShow: function() {
                this.$('#inputPackageName').focus();
            }

        });
    });