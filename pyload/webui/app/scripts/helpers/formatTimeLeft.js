// Format seconds in human readable format
define('helpers/formatTimeLeft', ['handlebars', 'vendor/remaining'], function(Handlebars, Remaining) {
    'use strict';

    function formatTimeLeft(seconds, options) {
        if (seconds === Infinity)
            return '∞';
        else if (!seconds || seconds <= 0)
            return '-';

        // TODO: digital or written string
        return Remaining.getStringDigital(seconds, window.dates);
    }

    Handlebars.registerHelper('formatTimeLeft', formatTimeLeft);
    return formatTimeLeft;
});
