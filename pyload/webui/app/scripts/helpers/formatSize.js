// Format bytes in human readable format
define('helpers/formatsize', ['handlebars', 'utils/i18n'], function(Handlebars, i18n) {
  'use strict';

  var sizes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB'];
  function formatsize(bytes, options, multiplier) {
    //multiplier 1024 is used for trafficleft because trafficleft is in KiB
    if (typeof multiplier === 'number')
       bytes = bytes * multiplier;

    if (!bytes || bytes === 0) return '0 B';
    if (bytes === -1)
      return i18n.gettext('not available');
    if (bytes === -2)
      return i18n.gettext('unlimited');

    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)), 10);
    // round to two digits
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
  }

  Handlebars.registerHelper('formatsize', formatsize);
  return formatsize;
});
