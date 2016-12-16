// Formats a timestamp
define('helpers/formatTime', ['underscore','handlebars', 'moment', 'utils/i18n'],
    function(_, Handlebars, moment, i18n) {
    'use strict';

    function formatTime(time, format) {
        if (time === -1)
            return i18n.gettext('unknown');
        else if (time === -2)
            return i18n.gettext('unlimited');

        if (!_.isString(format))
            format = 'lll';

        return moment(time).format(format);
    }

    Handlebars.registerHelper('formatTime', formatTime);
    return formatTime;
});
