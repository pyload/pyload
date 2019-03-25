{% autoescape true %}

document.addEvent("domready", function() {
    var ul = new Element('ul#twitter_update_list');
    var script1 = new Element('script[src=http://twitter.com/javascripts/blogger.js][type=text/javascript]');
    var script2 = new Element('script[src=http://twitter.com/statuses/user_timeline/pyLoad.json?callback=twitterCallback2&count=6][type=text/javascript]');
    $("twitter").adopt(ul, script1, script2);
});

{% endautoescape %}
