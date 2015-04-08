# -*- coding: utf-8 -*-
#
# Test links:
# http://www.solidfiles.com/d/609cdb4b1b

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class solidfiles(SimpleHoster):
    __name__    = "solidfiles"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http:\/\/(?:www\.)?solidfiles\.com\/\w+\/(\w)+\/(\w|.|\d)*'

    __description__ = """ solidfiles.com hoster plugin """
    __license__     = "GPLv3"
    __authors__     = [("sraedler", "simon.raedler@yahoo.de")]


    NAME_PATTERN = r'<h1 title="(?P<N>(\w|\d|\.)+)"'
    SIZE_PATTERN = r'<p class="meta">(?P<S>(\d|\.)+) (?P<U>(\w)+)'
    OFFLINE_PATTERN = r'<h1>404<\/h1>'

    LINK_FREE_PATTERN = r'id="ddl-text" href="(https:\/\/(\w|\d|\.|\/)+)"'

    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1


    def handleFree(self, pyfile):
        # Search for Download URL
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))
	self.logDebug("Downloadlink: " + m.group(1))
	self.download(m.group(1))
	
getInfo = create_getInfo(solidfiles)