// Resolves name of plugin to icon path
define('helpers/pluginIcon', ['handlebars', 'app'], function(Handlebars, App) {
    'use strict';

    function pluginIcon(name) {
        if (name && typeof name === 'object' && typeof name.get === 'function')
            name = name.get('plugin');

        return App.apiUrl('icons/' + name);
    }

    Handlebars.registerHelper('pluginIcon', pluginIcon);
    return pluginIcon;
});
