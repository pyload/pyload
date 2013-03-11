// Format bytes in human readable format
define('helpers/formatTime', ['handlebars', 'utils/remaining'], function(Handlebars, Remaining) {


    function formatTime(seconds, options) {
        if (seconds === Infinity)
            return '∞';
        else if (!seconds || seconds <= 0)
            return "-";

        // TODO: digital or written string
        return Remaining.getStringDigital(seconds, window.dates);
    }

    Handlebars.registerHelper('formatTime', formatTime);
    return formatTime;
});