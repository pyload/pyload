define('helpers/ifeq', ['underscore', 'handlebars'],
  function(_, Handlebars) {
    /*jshint validthis:true */
    'use strict';
    function ifEq(v1, v2, options) {
      if (v1 === v2) {
        return options.fn(this);
      }
      return options.inverse(this);
    }

    Handlebars.registerHelper('ifEq', ifEq);
    return ifEq;
  });
