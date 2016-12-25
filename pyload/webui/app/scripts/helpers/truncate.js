define(['underscore','handlebars'], function(_, Handlebars) {
  'use strict';

  function truncate(fullStr, options) {
    var strLen = 30;
    if (_.isNumber(options))
      strLen = options;

    if (!fullStr || fullStr.length <= strLen) return fullStr;

    var separator = options.separator || '…';

    var sepLen = separator.length,
      charsToShow = strLen - sepLen,
      frontChars = Math.ceil(charsToShow / 2),
      backChars = Math.floor(charsToShow / 2);

    return fullStr.substr(0, frontChars) +
      separator +
      fullStr.substr(fullStr.length - backChars);
  }

  Handlebars.registerHelper('truncate', truncate);
  return truncate;
});
