define(['jquery', 'backbone', 'underscore'], function($, Backbone, _) {

    // Renders input elements
    return Backbone.View.extend({

        tagName: 'input',

        model: null,
        value: null,
        default_value: null,
        description: null,

        initialize: function(model, value, default_value, description) {
            this.model = model;
            this.value = value;
            this.default_value = default_value;
            this.description = description;
        },

        render: function() {
            return this;
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