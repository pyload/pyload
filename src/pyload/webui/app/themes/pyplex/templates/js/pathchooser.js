{% autoescape true %}

var submit = true;
{% if absolute %}
var cwd = "{{oldfile|default(cwd, True)|abspath|quotepath|replace('\\', '\\\\')}}";
var isabsolute = true;
{% else %}
var cwd = "{{oldfile|default(cwd, True)|relpath|quotepath|replace('\\', '\\\\')}}";
var isabsolute = false;
{% endif %}

{% if type == 'folder' %} {# browsing for folder #}
var abspath = "/pathchooser/{{cwd|abspath|quotepath|replace('\\', '\\\\')}}";
var relpath = "/pathchooser/{{cwd|relpath|quotepath|replace('\\', '\\\\')}}";
{% else %} {# browsing for file #}
var abspath = "/filechooser/{{oldfile|default(cwd, True)|abspath|quotepath|replace('\\', '\\\\')}}";
var relpath = "/filechooser/{{oldfile|default(cwd, True)|relpath|quotepath|replace('\\', '\\\\')}}";
{% endif %}

document.addEventListener("readystatechange", function(event) {
  if (this.readyState === "complete") {
    document.getElementById("tbody").style.height = (window.innerHeight - 25) + "px";
    window.onresize = function (event) {
      document.getElementById("tbody").style.height = (window.innerHeight - 25) + "px";
    };
    var clickables = document.getElementsByClassName("tr-clickable");
    for (var i = 0; i < clickables.length; i++) {
      clickables[i].onclick = (function () {
        var onclick = clickables[i].onclick;
        return function (e) {
          if (onclick != null && !onclick()) {
              return false
          }
          if (this.dataset.href !== undefined && this.dataset.href !== "#") {
              window.location.href = this.dataset.href;
              return false
          } else {
              return true;
          }
        }
      })();
    }
  }
});
function updateParent()
{
    if (window.top.SettingsUI != undefined) {
        window.top.SettingsUI.prototype.pathchooserChanged(this);
    }
}
function setInvalid() {
    submit = false;
    cwd = "";
    updateParent();
}
function setValid() {
    submit = true;
    updateParent();
}
function setFile(fullpath, name)
{
    cwd = fullpath;
    {% if type == "file" %} {# browsing for file #}
      abspath = "/filechooser/{{cwd|abspath|quotepath|replace('\\', '\\\\')}}" + name;
      relpath = "/filechooser/{{cwd|relpath|quotepath|replace('\\', '\\\\')}}" + name;
    {% endif %}
    setValid();
}

{% endautoescape %}
