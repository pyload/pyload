function getXmlHttpRequestObject() {
    if (window.XMLHttpRequest) {
        return new XMLHttpRequest(); //Not IE
    } else if(window.ActiveXObject) {
        return new ActiveXObject("Microsoft.XMLHTTP"); //IE
    } else {
        alert("Your browser doesn't support the XmlHttpRequest object.  Better upgrade to Firefox.");
    }
}
var req = getXmlHttpRequestObject();

function getDownloads() {
    req.onreadystatechange = function() {
        if (req.readyState == 4) {
            if(req.status==200) {
                document.getElementById('downloads').innerHTML = req.responseText;
            } else {
                alert("Fehler:\nHTTP-Status: "+req.status+"\nHTTP-Statustext: "+req.statusText);
            }
        };
    }
    req.open("GET", '/downloads', true);
    req.send(null);
}

function addUrl(new_url) {
    req.onreadystatechange = function() {
        if (req.readyState == 4) {
            if(req.status==200) {
                document.getElementById('add_urls').innerHTML = req.responseText;
            } else {
                alert("Fehler:\nHTTP-Status: "+req.status+"\nHTTP-Statustext: "+req.statusText);
            }
        };
    }
    url = "/add=" + new_url
    req.open("GET", url, true);
    req.send(null);
}

window.setInterval("getDownloads()", 1000);

