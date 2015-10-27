# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class TNTVillageScambioeticoOrg(SimpleCrypter):
    __name__    = "TNTVillageScambioeticoOrg"
    __type__    = "crypter"
    __version__ = "0.05"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?forum\.tntvillage\.scambioetico\.org/index\.php\?.*showtopic=\d+'
    __config__  = [("activated"            , "bool", "Activated"                                        , True),
                   ("use_premium"          , "bool", "Use premium account if available"                 , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"                        , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package"              , True),
                   ("max_wait"             , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """TNTVillage.scambioetico.org decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERNS = [r'<th class="titlemedium"><a href=\'(.+?)\'', r"<a href='(\./index\.php\?act.+?)'"]


    def get_links(self):
        for p in self.LINK_PATTERNS:
            self.LINK_PATTERN = p
            links = super(TNTVillageScambioeticoOrg, self).getLinks()
            if links:
                return links


getInfo = create_getInfo(TNTVillageScambioeticoOrg)
