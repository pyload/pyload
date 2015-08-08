# -*- coding: utf-8 -*-

from module.plugins.internal.Crypter import Crypter


class XupPl(Crypter):
    __name__    = "XupPl"
    __type__    = "crypter"
    __version__ = "0.12"
    __status__  = "testing"

    __pattern__ = r'https?://(?:[^/]*\.)?xup\.pl/.+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Xup.pl decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("z00nx", "z00nx0@gmail.com")]


    def decrypt(self, pyfile):
        header = self.load(pyfile.url, just_header=True)
        if 'location' in header:
            self.urls = [header['location']]
        else:
            self.fail(_("Unable to find link"))
