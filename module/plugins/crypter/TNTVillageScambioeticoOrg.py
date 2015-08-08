# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class TNTVillageScambioeticoOrg(SimpleCrypter):
    __name__    = "TNTVillageScambioeticoOrg"
    __type__    = "crypter"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?forum\.tntvillage\.scambioetico\.org/index\.php\?.*showtopic=\d+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),  #: Overrides pyload.config['general']['folder_per_package']
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

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
