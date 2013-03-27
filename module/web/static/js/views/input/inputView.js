define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    // Renders input elements
    return Backbone.View.extend({

        tagName: 'input',

        model: null,
        value: null,
        default_value: null,
        description: null,

        // enables tooltips
        tooltip: true,

        initialize: function(model, value, default_value, description) {
            this.model = model;
            this.value = value;
            this.default_value = default_value;
            this.description = description;
        },

        render: function() {
            this.renderInput();
            // data for tooltips
            if (this.description && this.tooltip) {
                this.$el.data('content', this.description);
                // TODO: render default value in popup?
//                this.$el.data('title', "TODO: title");
                this.$el.popover({
                    placement: 'right',
                    trigger: 'hover',
//                    delay: { show: 500, hide: 100 }
                });
            }

            return this;
        },

        renderInput: function() {
            // Overwrite this
        },

        showTooltip: function() {
            if (this.description && this.tooltip)
                this.$el.popover('show');
        },

        hideTooltip: function() {
            if (this.description && this.tooltip)
                this.$el.popover('hide');
        },

        destroy: function() {
            this.undelegateEvents();
            this.unbind();
            if (this.onDestroy) {
                this.onDestroy();
            }
            this.$el.removeData().unbind();
            this.remove();
        },

        // focus the input element
        focus: function() {
            this.$el.focus();
        },

        // Clear the input
        clear: function() {

        },

        // retrieve value of the input
        getVal: function() {
            return this.value;
        },

        // the child class must call this when the value changed
        setVal: function(value) {
            this.value = value;
            this.trigger('change', value);
        }
    });
});