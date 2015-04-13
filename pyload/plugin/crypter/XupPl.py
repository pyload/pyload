# -*- coding: utf-8 -*-

from pyload.plugin.Crypter import Crypter


class XupPl(Crypter):
    __name    = "XupPl"
    __type    = "crypter"
    __version = "0.10"

    __pattern = r'https?://(?:[^/]*\.)?xup\.pl/.+'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Xup.pl decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("z00nx", "z00nx0@gmail.com")]


    def decrypt(self, pyfile):
        header = self.load(pyfile.url, just_header=True)
        if 'location' in header:
            self.urls = [header['location']]
        else:
            self.fail(_("Unable to find link"))
