define(['jquery', 'underscore', 'transit'], function(jQuery, _) {

    // Overwrite common animations with transitions
    jQuery.each({
        fadeIn: { opacity: "show" },
        fadeOut: { opacity: "hide" }
    }, function(name, props) {
        jQuery.fn[ name ] = function(speed, easing, callback) {
            return this.transition(props, speed, easing, callback);
        };
    });

    // TODO: sloppy chaining
    // in functions not possible without previous out

    jQuery.fn.zapIn = function(speed, easing, callback) {
        var height = this.data('height') || '100%';
        this.transition({
            height: height,
            scale: [1, 1],
            opacity: 'show'
        }, speed, easing, callback);

    };

    jQuery.fn.zapOut = function(speed, easing, callback) {
        if (!this.data('height')) {
            var height = this.height();
            this.css({height: height});
            this.data('height', height)
        }
        this.transition({
            height: '0px',
            scale: [1, 0],
            opacity: 'hide'
        }, speed, easing, callback);

    };

    jQuery.fn.slideIn = function(speed, easing, callback) {
        var height = this.data('height') || '100%';
        this.transition({
            height: height,
            opacity: 'show'
        }, speed, easing, callback);

    };

    jQuery.fn.slideOut = function(speed, easing, callback) {
        if (!this.data('height')) {
            var height = this.height();
            this.css({height: height, overflow: 'hidden'});
            this.data('height', height)
        }
        this.transition({
            height: '0px',
            opacity: 'hide'
        }, speed, easing, callback);

    };

    jQuery.fn._transit = jQuery.fn.transit;

    // Overriding transit plugin to support hide and show
    // Props retains it properties across multiple calls, therefore props.show value is introduced
    jQuery.fn.transit = jQuery.fn.transition = function(props, duration, easing, callback) {
        var self = this;
        var cb = callback;
        if (props && (props.opacity === 'hide' || (props.opacity === 0 && props.show === true))) {
            props.opacity = 0;
            props.show = true;

            callback = function() {
                self.css({display: 'none'});
                if (typeof cb === 'function') {
                    cb.apply(self);
                }
            };
        } else if (props && (props.opacity === 'show' || (props.opacity === 1 && props.show === true))) {
            props.opacity = 1;
            props.show = true;
            this.css({display: 'block'});
        }

        return this._transit(props, duration, easing, callback);
    };
});