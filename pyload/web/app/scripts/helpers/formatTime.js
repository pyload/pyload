// Format bytes in human readable format
define('helpers/formatTime', ['handlebars', 'vendor/remaining'], function(Handlebars, Remaining) {
    'use strict';

    function formatTime(seconds, options) {
        if (seconds === Infinity)
            return '∞';
        else if (!seconds || seconds <= 0)
            return '-';

        // TODO: digital or written string
        return Remaining.getStringDigital(seconds, window.dates);
    }

    Handlebars.registerHelper('formatTime', formatTime);
    return formatTime;
});