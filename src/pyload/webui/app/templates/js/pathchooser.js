{% autoescape true %}

function chosen() {
    opener.ifield.value = document.forms[0].p.value;
    close();
}
function exit() {
    close();
}
function setInvalid() {
    document.forms[0].send.disabled = 'disabled';
    document.forms[0].p.style.color = '#FF0000';
}
function setValid() {
    document.forms[0].send.disabled = '';
    document.forms[0].p.style.color = '#000000';
}
function setFile(file) {
    document.forms[0].p.value = file;
    setValid();
}

{% endautoescape %}
