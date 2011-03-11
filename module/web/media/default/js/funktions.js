// JavaScript Document
function HumanFileSize(size) {
    var filesizename = new Array("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB");
    var loga = Math.log(size) / Math.log(1024);
    var i = Math.floor(loga);
    var a = Math.pow(1024, i);
    return (size == 0) ? "0 B" : (Math.round(size / a, 2) + " " + filesizename[i]);
}

function parseUri() {
    var oldString = $("add_links").value;
    var regxp = new RegExp('(ht|f)tp(s?):\/\/[a-zA-Z0-9\-\.\/\?=_&%#]+[<| |\"|\'|\r|\n|\t]{1}', 'g');
    var resu = oldString.match(regxp);
    if (resu == null) return;
    var res = "";
    for (var i = 0; i < resu.length; i++) {
        // remove the last char, if ...
        if (resu[i].indexOf(" ") != -1) {
            res = res + resu[i].replace(" ", " \n");
        } else if (resu[i].indexOf("\t") != -1) {
            res = res + resu[i].replace("\t", " \n");
        } else if (resu[i].indexOf("\r") != -1) {
            res = res + resu[i].replace("\r", " \n");
        } else if (resu[i].indexOf("\"") != -1) {
            res = res + resu[i].replace("\"", " \n");
        } else if (resu[i].indexOf("<") != -1) {
            res = res + resu[i].replace("<", " \n");
        } else if (resu[i].indexOf("'") != -1) {
            res = res + resu[i].replace("'", " \n");
        } else {
            res = res + resu[i].replace("\n", " \n");
        }
    }
    $("add_links").value = res;
}

Array.prototype.remove = function(from, to) {
    var rest = this.slice((to || from) + 1 || this.length);
    this.length = from < 0 ? this.length + from : from;
    if (this.length == 0) return [];
    return this.push.apply(this, rest);
};