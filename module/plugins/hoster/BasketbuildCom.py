# -*- coding: utf-8 -*
#
# Test links:
#   https://s.basketbuild.com/filedl/devs?dev=pacman&dl=pacman/falcon/RC-3/pac_falcon-RC-3-20141103.zip
#   https://s.basketbuild.com/filedl/gapps?dl=gapps-gb-20110828-signed.zip

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class BasketbuildCom(SimpleHoster):
    __name__    = "BasketbuildCom"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?\w.basketbuild.com/filedl/.+'

    __description__ = """basketbuild.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'File Name:</strong> (?P<N>.*?)<br/>'
    SIZE_PATTERN    = r'File Size:</strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)<br/>'
    OFFLINE_PATTERN = r'404 - Page Not Found'


    def setup(self):
        self.multiDL        = True
        self.resumeDownload = True
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        link1 = re.search(r'href="(.+dlgate/.+)"',self.html)
        try:
            self.logDebug("Next hop: %s" % link1.group(1))
            self.html = self.load(link1.group(1), cookies=True)
        except AttributeError:
            self.error(_("Hop #1 not found"))
            
        wait = re.search(r'var sec = (\d+);',self.html)
        try:
            self.logDebug("Wait %s seconds" % wait.group(1))
            self.wait(wait.group(1))
        except AttributeError:
            self.logDebug("No wait time found")
        
        link2 = re.search(r'id="dlLink">\s*<a href="(.*?)"',self.html)
        try:
            self.logDebug("DL-Link: %s" % link2.group(1))
        except AttributeError:
            self.error(_("DL-Link not found"))
        
        self.download(link2.group(1), cookies=True, disposition=True)


getInfo = create_getInfo(BasketbuildCom)
