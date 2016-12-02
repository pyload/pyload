define(['jquery', 'underscore', 'transit'], function(jQuery, _) {
    'use strict';

    // Adds an element and computes its height, which is saved as data attribute
    // Important function to have slide animations
    jQuery.fn.appendWithHeight = function(element, hide) {
        var o = jQuery(this[0]);
        element = jQuery(element);

        // TODO: additionally it could be placed out of viewport first
        // The real height can only be retrieved when element is on DOM and display:true
        element.css('visibility', 'hidden');
        o.append(element);

        var height = element.height();

        // Hide the element
        if (hide === true) {
            element.hide();
            element.height(0);
        }

        element.css('visibility', '');
        element.data('height', height);

        return this;
    };

    // Shortcut to have a animation when element is added
    jQuery.fn.appendWithAnimation = function(element, animation) {
        var o = jQuery(this[0]);
        element = jQuery(element);

        if (animation === true)
            element.hide();

        o.append(element);

        if (animation === true)
            element.fadeIn();

//        element.calculateHeight();

        return this;
    };

    // calculate the height and write it to data, should be used on invisible elements
    jQuery.fn.calculateHeight = function(setHeight) {
        var o = jQuery(this[0]);
        var height = o.height();
        if (!height) {
            var display = o.css('display');
            o.css('visibility', 'hidden');
            o.show();
            height = o.height();

            o.css('display', display);
            o.css('visibility', '');
        }

        if (setHeight)
            o.css('height', height);

        o.data('height', height);
        return this;
    };

    // TODO: carry arguments, optional height argument

    // reset arguments, sets overflow hidden
    jQuery.fn.slideOut = function(reset) {
        var o = jQuery(this[0]);
        o.animate({height: o.data('height'), opacity: 'show'}, function() {
            // reset css attributes;
            if (reset) {
                this.css('overflow', '');
                this.css('height', '');
            }
        });
        return this;
    };

    jQuery.fn.slideIn = function(reset) {
        var o = jQuery(this[0]);
        if (reset) {
            o.css('overflow', 'hidden');
        }
        o.animate({height: 0, opacity: 'hide'});
        return this;
    };

    jQuery.fn.initTooltips = function(placement) {
        placement || (placement = 'top');

        var o = jQuery(this[0]);
        o.find('[data-toggle="tooltip"]').tooltip(
            {
                delay: {show: 800, hide: 100},
                placement: placement
            });

        return this;
    };

    jQuery.fn._transit = jQuery.fn.transit;

    // Overriding transit plugin to support hide and show
    jQuery.fn.transit = jQuery.fn.transition = function(props, duration, easing, callback) {
        var self = this;
        var cb = callback;
        var newprops = _.extend({}, props);

        if (newprops && (newprops.opacity === 'hide')) {
            newprops.opacity = 0;

            callback = function() {
                self.css({display: 'none'});
                if (typeof cb === 'function') {
                    cb.apply(self);
                }
            };
        } else if (newprops && (newprops.opacity === 'show')) {
            newprops.opacity = 1;
            this.css({display: 'block'});
        }

        return this._transit(newprops, duration, easing, callback);
    };
});
