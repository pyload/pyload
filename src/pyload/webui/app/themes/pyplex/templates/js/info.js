{% autoescape true %}

function () {
  $.ajax({
      type: 'GET',
      url: "https://script.google.com/macros/s/AKfycbwXJoDipzpsyYPx58-s33WA4nYJLwD3VouY2zwKcCZNsxCTvUQ/exec",
      dataType: "jsonp",
      context: {},
      success: function (data) {
        if (data.proxy.error === undefined && data.responseCode === 200) {
          var el = $('<div></div>');
          el.html(data.result);
          var result = ["", ""];
          var tweets = $('div.tweet', el).slice(0,10);
          tweets.each(function (i, s) {
              var $node = $(s);
              var link = "https://mobile.twitter.com" + $node.data("permalinkPath") +"&p=v";
              var text = $node.find("p.tweet-text") .clone().children().remove().end().text();
              var $timestamp = $node.find(".js-short-timestamp");
              var timestamp = $timestamp.length ? $timestamp.text() : 'N/A';
              result[i % 2] += '<span class="noselect" style="font-size: 10px;">' + timestamp + '</span><a href="' + link +'" target="_blank" ondragstart="return false;">' + text + '</a>';
          });
          $("#twitter").html('<div class="col-xs-12 col-sm-6 col-md-6 col-lg-6">\n' +
                             '<div id="col0"></div>\n' +
                             '</div>\n' +
                             '<div class="col-xs-12 col-sm-6 col-md-6 col-lg-6">\n' +
                             '<div id="col1"></div>\n' +
                             '</div>\n');
          $('#col0').html(result[0]);
          $('#col1').html(result[1]);
        }
      }
  });
}

{% endautoescape %}
