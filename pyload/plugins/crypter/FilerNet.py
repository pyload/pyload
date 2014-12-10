import re

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class FilerNet(SimpleCrypter):
    __name    = "FilerNet"
    __type    = "crypter"
    __version = "0.41"

    __pattern = r'https?://filer\.net/folder/\w{16}'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Filer.net decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'href="(/get/\w{16})">(?!<)'
    NAME_PATTERN = r'<h3>(?P<N>.+?) - <small'


    def getLinks(self):
        return ['http://filer.net%s' % link for link in re.findall(self.LINK_PATTERN, self.html)]
