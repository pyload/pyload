// Loads all helper and set own handlebars rules
define(['jquery', 'underscore', 'views/abstract/modalView'], function($, _, Modal) {
    'use strict';

    // Shows the confirm dialog for given context
    // on success executes func with context
    _.confirm = function(template, func, context) {
        template = 'hbs!tpl/' + template;
        _.requireOnce([template], function(html) {
            var dialog = new Modal(html, _.bind(func, context));
            dialog.show();
        });

    };
});
