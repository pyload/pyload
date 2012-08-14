// jQuery OmniWindow plugin
// @version:  0.7.0
// @author:   Rudenka Alexander (mur.mailbox@gmail.com)
// @license:  MIT

;(function($) {
  "use strict";
  $.fn.extend({
    omniWindow: function(options) {

      options = $.extend(true, {
        animationsPriority: {
          show: ['overlay', 'modal'],
          hide: ['modal', 'overlay']
        },
        overlay: {
          selector: '.ow-overlay',
          hideClass: 'ow-closed',
          animations: {
            show: function(subjects, internalCallback) { return internalCallback(subjects); },
            hide: function(subjects, internalCallback) { return internalCallback(subjects); },
            internal: {
              show: function(subjects){ subjects.overlay.removeClass(options.overlay.hideClass); },
              hide: function(subjects){ subjects.overlay.addClass(options.overlay.hideClass); }
            }
          }
        },
        modal:   {
          hideClass: 'ow-closed',
          animations: {
            show: function(subjects, internalCallback) { return internalCallback(subjects); },
            hide: function(subjects, internalCallback) { return internalCallback(subjects); },
            internal: {
              show: function(subjects){ subjects.modal.removeClass(options.modal.hideClass); },
              hide: function(subjects){ subjects.modal.addClass(options.modal.hideClass); }
            }
          },
          internal: {
            stateAttribute: 'ow-active'
          }
        },
        eventsNames: {
          show: 'show.ow',
          hide: 'hide.ow',
          internal: {
            overlayClick:  'click.ow',
            keyboardKeyUp: 'keyup.ow'
          }
        },
        callbacks: {                                                                                  // Callbacks execution chain
          beforeShow:  function(subjects, internalCallback) { return internalCallback(subjects); },   // 1 (stop if retruns false)
          positioning: function(subjects, internalCallback) { return internalCallback(subjects); },   // 2
          afterShow:   function(subjects, internalCallback) { return internalCallback(subjects); },   // 3
          beforeHide:  function(subjects, internalCallback) { return internalCallback(subjects); },   // 4 (stop if retruns false)
          afterHide:   function(subjects, internalCallback) { return internalCallback(subjects); },   // 5
          internal: {
            beforeShow: function(subjects) {
              if (subjects.modal.data(options.modal.internal.stateAttribute)) {
                return false;
              } else {
                subjects.modal.data(options.modal.internal.stateAttribute, true);
                return true;
              }
            },
            afterShow: function(subjects) {
              $(document).on(options.eventsNames.internal.keyboardKeyUp, function(e) {
                if (e.keyCode === 27) {                                              // if the key pressed is the ESC key
                  subjects.modal.trigger(options.eventsNames.hide);
                }
              });

              subjects.overlay.on(options.eventsNames.internal.overlayClick, function(){
                subjects.modal.trigger(options.eventsNames.hide);
              });
            },
            positioning: function(subjects) {
              subjects.modal.css('margin-left', Math.round(subjects.modal.outerWidth() / -2));
            },
            beforeHide: function(subjects) {
              if (subjects.modal.data(options.modal.internal.stateAttribute)) {
                subjects.modal.data(options.modal.internal.stateAttribute, false);
                return true;
              } else {
                return false;
              }
            },
            afterHide: function(subjects) {
              subjects.overlay.off(options.eventsNames.internal.overlayClick);
              $(document).off(options.eventsNames.internal.keyboardKeyUp);

              subjects.overlay.css('display', ''); // clear inline styles after jQ animations
              subjects.modal.css('display', '');
            }
          }
        }
      }, options);

      var animate = function(process, subjects, callbackName) {
        var first  = options.animationsPriority[process][0],
            second = options.animationsPriority[process][1];

        options[first].animations[process](subjects, function(subjs) {        // call USER's    FIRST animation (depends on priority)
          options[first].animations.internal[process](subjs);                 // call internal  FIRST animation

          options[second].animations[process](subjects, function(subjs) {     // call USER's    SECOND animation
            options[second].animations.internal[process](subjs);              // call internal  SECOND animation

                                                                              // then we need to call USER's
                                                                              // afterShow of afterHide callback
            options.callbacks[callbackName](subjects, options.callbacks.internal[callbackName]);
          });
        });
      };

      var showModal = function(subjects) {
        if (!options.callbacks.beforeShow(subjects, options.callbacks.internal.beforeShow)) { return; } // cancel showing if beforeShow callback return false

        options.callbacks.positioning(subjects, options.callbacks.internal.positioning);

        animate('show', subjects, 'afterShow');
      };

      var hideModal = function(subjects) {
        if (!options.callbacks.beforeHide(subjects, options.callbacks.internal.beforeHide)) { return; } // cancel hiding if beforeHide callback return false

        animate('hide', subjects, 'afterHide');
      };


      var $overlay = $(options.overlay.selector);

      return this.each(function() {
        var $modal  = $(this);
        var subjects = {modal: $modal, overlay: $overlay};

        $modal.bind(options.eventsNames.show, function(){ showModal(subjects); })
              .bind(options.eventsNames.hide, function(){ hideModal(subjects); });
      });
    }
  });
})(jQuery);