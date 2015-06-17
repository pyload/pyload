# -*- coding: utf-8 -*-

from module.plugins.internal.Hook import Hook, Expose

class WebinterfaceReconnectToggle(Hook):
    __name__    = "WebinterfaceReconnectToggle"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("activated", "bool", "Activated", True )]

    __description__ = """Toggle reconnect settings by clicking on the reconnect status text in Webinterface's information box."""
    __license__     = "GPLv3"
    __authors__     = [("Matthias Nippert", "matthias@dornuweb.de")]

    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10

    @Expose
    def webinterface_add_plugin_content(self):
        my_javascript = """
document.addEvent("domready", function() {
    $("reconnect").set('href', '/api/toggleReconnect');
    $("reconnect").parentElement.addEvent('click', function(){
        new Request.JSON({
            url: "/api/toggleReconnect", secure: false, async: true,
        }).send();
        $("reconnect").set('text', ' ...');
        $("reconnect").setStyle('background-color', "#cccccc");
        return false;
    });
}, false );
"""
        my_css = """
.reconnect, #reconnect {
    cursor: pointer; 
    cursor: hand;
}
.reconnect:hover, #reconnect:hover {
    text-decoration: underline;
}
"""
        content = [
            {"type":"javascript", "content": my_javascript},
            {"type":"css", "content": my_css}
        ]
        return content
