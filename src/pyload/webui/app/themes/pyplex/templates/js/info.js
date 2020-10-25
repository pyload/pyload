{% autoescape true %}

Date.prototype.toFormattedString = function () {
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][this.getMonth()-1] +
        "," + String(this.getDate()) +
        ", " + String(this.getFullYear());
};

function renderTweetHtml(tweet) {
    //Convert \n into <br>
    let html = tweet.full_text.replaceAll("\n", "<br>");
    //Add link to all URLs within tweets
    let i = 1;
    html = html.replace(/(?:https?|s?ftp|ssh):\/\/[^"\s<>]*[^.,;'">:\s<>)\]!]/g, function(url) {
        let result = '';
        for (let u of tweet.entities.urls) {
            if (u.url === url) {
                if (i === 1 && u.expanded_url.match(/^https:\/\/github.com\/pyload\/[^\/]+\/commit\//)) {
                    result = '';
                } else {
                    result = '<a href="'+ u.expanded_url + '" target="_blank" ondragstart="return false;">' + u.display_url + '</a>';
                }
                break;
            }
        }
        i+=1;
        return result;
    });
    //Add link to @usernames used within tweets
    html = html.replace(/\B@[_a-z0-9]+/ig, function(user) {
        return '<a href="http://twitter.com/'+user.substring(1)+'" target="_blank" ondragstart="return false;">'+user+'</a>';
    });
    html = html.replace(/\B#[_a-z0-9]+/ig, function(obj) {
        if (obj.match(/\B#\d{1,4}(?:[^\d]|$)/)) {
            //Add link to github #issuenumber used within tweets
            return '<a href="https://github.com/pyload/pyload/issues/'+obj.substring(1)+'" target="_blank" ondragstart="return false;">'+obj+'</a>';
        } else {
            //Add link to #hastag used within tweets
            return '<a href="https://twitter.com/search?q=' + obj.substring(1) + '" target="_blank" ondragstart="return false;">' + obj + '</a>';
        }
    });
    return html;
}

$(function () {
  $.ajax({
      type: 'GET',
      url: "https://script.google.com/macros/s/AKfycbwXJoDipzpsyYPx58-s33WA4nYJLwD3VouY2zwKcCZNsxCTvUQ/exec",
      dataType: "jsonp",
      context: {},
      success: function (data) {
        if (data.proxy.error === undefined && data.responseCode === 200) {
            var tweets = JSON.parse(data.result);
            var result = ["", ""];
            tweets.forEach(function (tweet, i) {
                var link = "https://twitter.com/pyload/status/" + tweet.id_str;
                var html = renderTweetHtml(tweet);
                var timestamp = new Date(tweet.created_at);
              result[i % 2] += '<span class="noselect" style="font-size: 10px;">' + timestamp.toFormattedString() + '</span><p onclick="var win=window.open(\'' + link + '\', \'_blank\');win.focus();">' + html + '</p>';
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
});

{% endautoescape %}
