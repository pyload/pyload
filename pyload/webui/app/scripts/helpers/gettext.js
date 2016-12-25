define(['underscore', 'handlebars', 'utils/i18n'], function(_, Handlebars, i18n) {
  'use strict';
  // These methods binds additional content directly to translated message
  function ngettext(single, plural, n) {
    return i18n.sprintf(i18n.ngettext(single, plural, n), n);
  }

  function gettext(key, message) {
    return i18n.sprintf(i18n.gettext(key), message);
  }

  Handlebars.registerHelper('_', gettext);
  Handlebars.registerHelper('gettext', gettext);
  Handlebars.registerHelper('ngettext', ngettext);
  return gettext;
});
