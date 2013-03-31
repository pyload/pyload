define(['jquery', 'underscore', 'app', 'views/abstract/modalView', 'text!tpl/default/accountDialog.html', 'select2'],
    function($, _, App, modalView, template) {
        return modalView.extend({

            events: {
                'click .btn-add': 'add'
            },
            template: _.compile(template),
            plugins: null,
            select: null,

            initialize: function() {
                // Inherit parent events
                this.events = _.extend({}, modalView.prototype.events, this.events);
                var self = this;
                $.ajax(App.apiRequest('getAccountTypes', null, {success: function(data) {
                    self.plugins = _.sortBy(data, function(item) {
                        return item;
                    });
                    self.render();
                }}));
            },

            onRender: function() {
                // TODO: could be a seperate input type if needed on multiple pages
                if (this.plugins)
                    this.select = this.$('#pluginSelect').select2({
                        escapeMarkup: function(m) {
                            return m;
                        },
                        formatResult: this.format,
                        formatSelection: this.format,
                        data: {results: this.plugins, text: function(item) {
                            return item;
                        }},
                        id: function(item) {
                            return item;
                        }
                    });
            },

            onShow: function() {
            },

            onHide: function() {
            },

            format: function(data) {
                return '<img class="logo-select" src="icons/' + data + '"> ' + data;
            },

            add: function(e) {
                e.stopPropagation();
                if (this.select) {
                    var plugin = this.select.val();
                    // TODO
                }
            }
        });
    });