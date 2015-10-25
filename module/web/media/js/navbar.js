document.addEvent("domready", function() {
   $$('.navbar-toggle').addEvent('click', function(e) {
        var button;
        if(e.target.hasClass('navbar-toggle')) {
            button = e.target;
        } else {
            button = e.target.getParent('.navbar-toggle');
        }
        var toggle = button.getProperty('data-toggle');
        var target = button.getProperty('data-target');
        $$(target).toggleClass(toggle);
    });
});

