# -*- coding: utf-8 -*-
import re

from os import remove
from os.path import exists
from urllib import quote

from module.plugins.Hoster import Hoster
from module.utils import fs_encode
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LineStorage(SimpleHoster):
    __name__ = "LineStorage"
    __type__ = "hoster"
    __version__ = "0.1"
    __pattern__ = r'https?://(?:www\.)?linestorage.com/.*'
    __description__ = """LineStorage.com hoster plugin"""
    __author_name__ = ("gsasch")
    __author_mail__ = ("")

    def setup(self):
        self.resumeDownload = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Uploadable.ch")
            self.fail("No LineStorage account provided")

        self.logDebug("Old URL: %s" % pyfile.url)

        #raise timeout to 2min
        self.req.setOption("timeout", 120)
	
	self.html = self.load(self.pyfile.url)
	#self.log.warning(_("eccoci %s" % self.html))
	action, inputs = self.parseHtmlForm('name="f1')
        m = re.search(r'(?<=name="rand" value=")[^"]*' , self.html, re.I)
	rand = m.group(0)
	m = re.search(r'(?<=name="id" value=")[^"]*' , self.html, re.I)
	id = m.group(0)
			    
        self.download(self.pyfile.url, post={"op" : "download2", "id" : id, "rand" : rand, 
		"referer" : "", "method_free" : "", "method_premium" : "1",
		"down_direct" : "1", "btn_download": "Create Download Link"} )

