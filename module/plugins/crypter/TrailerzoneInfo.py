# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class TrailerzoneInfo(Crypter):
    __name__ = "TrailerzoneInfo"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?trailerzone.info/.*?"
    __version__ = "0.02"
    __description__ = """TrailerZone.info Crypter Plugin"""
    __author_name__ = ("godofdream")
    __author_mail__ = ("soilfiction@gmail.com")

    JS_KEY_PATTERN = r"<script>(.*)var t = window"

    def decrypt(self, pyfile):
        protectPattern = re.compile("http://(www\.)?trailerzone.info/protect.html.*?")
        goPattern = re.compile("http://(www\.)?trailerzone.info/go.html.*?")
        url = pyfile.url
        if protectPattern.match(url):
            self.handleProtect(url)
        elif goPattern.match(url):
            self.handleGo(url)
			
    def handleProtect(self, url):
        self.handleGo("http://trailerzone.info/go.html#:::" + url.split("#:::",1)[1])
			
    def handleGo(self, url):
        
        src = self.req.load(str(url))
        pattern = re.compile(self.JS_KEY_PATTERN, re.DOTALL)
        found = re.search(pattern, src)
        
        # Get package info 
        package_links = []  
        try:
            result = self.js.eval(found.group(1) + " decodeLink('" + url.split("#:::",1)[1] + "');")
            result = str(result)
            self.logDebug("RESULT: %s" % result)
            package_links.append(result)
            self.core.files.addLinks(package_links, self.pyfile.package().id)
        except Exception, e:
            self.logDebug(e)                                       
            self.fail('Could not extract any links by javascript')
