define(['jquery', 'underscore', './inputLoader'], function($, _, load_input) {
  'use strict';

  // Renders list of ConfigItems to an container
  // Optionally binds change event to view
  return function(container, items, template, onChange, view) {
    _.each(items, function(item) {
      var json = item.toJSON();
      var el = $('<div>').html(template(json));
      var InputView = load_input(item.get('input'));
      var input = new InputView(json).render();
      item.set('inputView', input);

      if (_.isFunction(onChange) && view) {
        view.listenTo(input, 'change', onChange);
      }

      el.find('.controls').append(input.el);
      container.append(el);
    });
  };
});
