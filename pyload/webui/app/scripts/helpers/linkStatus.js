define('helpers/linkStatus', ['underscore', 'handlebars', 'utils/apitypes', 'utils/i18n'],
    function(_, Handlebars, Api, i18n) {
        'use strict';
        function linkStatus(status) {
            var s;
            if (status === Api.DownloadStatus.Online)
                s = '<span class="text-success">' + i18n.gettext('online') + '</span>';
            else if (status === Api.DownloadStatus.Offline)
                s = '<span class="text-error">' + i18n.gettext('offline') + '</span>';
            else
                s = '<span class="text-info">' + i18n.gettext('unknown') + '</span>';

            return new Handlebars.SafeString(s);
        }

        Handlebars.registerHelper('linkStatus', linkStatus);
        return linkStatus;
    });
