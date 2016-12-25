define(['jquery', 'underscore', 'app', 'views/abstract/modalView', 'hbs!tpl/dialogs/editPackage'],
  function($, _, App, modalView, template) {
    'use strict';

    return modalView.extend({
      template: template,
      onHideDestroy: true,

      confirmCallback: function() {
        var self = this;
        this.$el.find('.input').each(function(i, el) {
          self.model.set($(el).data('attr'), $(el).val());
        });
        this.model.save();
      }

    });

  });
