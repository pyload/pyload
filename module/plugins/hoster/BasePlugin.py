#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class BasePlugin(Hoster):
    __name__ = "BasePlugin"
    __type__ = "hoster"
    __pattern__ = r"^unmatchable$"
    __version__ = "0.1"
    __description__ = """Base Plugin when any other didnt fit"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def process(self, pyfile):
        """main function"""
        
        #debug stuff
        
        res = self.decryptCaptcha("http://www.google.com/recaptcha/api/image?c=03AHJ_VusNo91yuOYR22VR2J2XUl4x8fqcKbKato005zKhc10DT8FmIP4WQwK_5QkJZVRdCNWDPSlASuS12Y30qMjBguJpYA9fztHKFE8Lp2FGOrl6EnMcgTeyx_6FuVpMstX_XRuhusH-Z6H3Tchsj077ptyDMOPFrg")
        print res
        
        #end
        
        if pyfile.url.startswith("http://"):

            pyfile.name = re.findall("([^\/=]+)", pyfile.url)[-1]
            self.download(pyfile.url)
            
        else:
            self.fail("No Plugin matched and not a downloadable url.")