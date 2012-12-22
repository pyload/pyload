define(['jquery', 'underscore', 'views/abstract/modalView', 'text!tpl/default/linkgrabber.html'],
    function($, _, modalView, template) {

    return modalView.extend({

        events: {
        },

        template: _.compile(template),

        initialize: function() {
            // Inherit parent events
            this.events = _.extend({}, modalView.prototype.events,this.events);
        },

        renderContent: function() {
            return $('<h1>Content!</h1>');
        }

    });
});