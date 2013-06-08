// Loads all helper and set own handlebars rules
define(['jquery', 'underscore', 'views/abstract/modalView'], function($, _, modal) {

    // Shows the confirm dialog for given context
    // on success executes func with context
    _.confirm = function(template, func, context) {
        template = "text!tpl/" + template;
        _.requireOnce([template], function(html) {
            var template = _.compile(html);
            var dialog = new modal(template, _.bind(func, context));
            dialog.show();
        });

    };
});