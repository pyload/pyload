# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN, Godofdream, zoidberg
"""
import time, httplib
from module.plugins.Hook import Hook

class WindowsPhoneToastNotify(Hook):
    __name__ = "WindowsPhoneToastNotify"
    __version__ = "0.02"
    __description__ = """Send push notifications to Windows Phone."""
    __author_name__ = ("Andy Voigt")
    __author_mail__ = ("phone-support@hotmail.de")
    __config__ = [("activated", "bool", "Activated", False),
                  ("force", "bool", "Force even if client is connected", False),
                  ("pushId", "str", "pushId", ""),
                  ("pushUrl","str","pushUrl", ""),
                  ("pushTimeout","int","Timeout between notifications in seconds","0")]

    def setup(self):
        self.info = {}
    
    def getXmlData(self):
        myxml = "<?xml version='1.0' encoding='utf-8'?> <wp:Notification xmlns:wp='WPNotification'> " \
                "<wp:Toast> <wp:Text1>Pyload Mobile</wp:Text1> <wp:Text2>Captcha waiting!</wp:Text2> " \
                "</wp:Toast> </wp:Notification>"
        return myxml

    def doRequest(self):
        URL = self.getConfig("pushUrl")
        request = self.getXmlData()
        webservice = httplib.HTTP(URL)
        webservice.putrequest("POST", self.getConfig("pushId"))
        webservice.putheader("Host", URL)
        webservice.putheader("Content-type", "text/xml")
        webservice.putheader("X-NotificationClass", "2")
        webservice.putheader("X-WindowsPhone-Target", "toast")
        webservice.putheader("Content-length", "%d" % len(request))
        webservice.endheaders()
        webservice.send(request)
        webservice.close()
        self.setStorage("LAST_NOTIFY", time.time())

    def newCaptchaTask(self, task):
        if not self.getConfig("pushId") or not self.getConfig("pushUrl"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False
        
        if (time.time() - float(self.getStorage("LAST_NOTIFY", 0))) < self.getConf("pushTimeout"):
            return False
        
        self.doRequest()

