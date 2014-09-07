# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class FiredriveComFolder(SimpleCrypter):
    __name__ = "FiredriveComFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?(firedrive|putlocker)\.com/share/.+'

    __description__ = """Firedrive.com folder decrypter plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    LINK_PATTERN = r'<div class="pf_item pf_(file|folder).+?public=\'(.+?)\''
    TITLE_PATTERN = r'>Shared Folder "(?P<title>.+)" | Firedrive<'
    OFFLINE_PATTERN = r'class="sad_face_image"|>No such page here.<'
    TEMP_OFFLINE_PATTERN = r'>(File Temporarily Unavailable|Server Error. Try again later)'


    def getLinks(self):
        return map(lambda x: "http://www.firedrive.com/%s/%s" %
                   ("share" if x[0] == "folder" else "file", x[1]),
                   re.findall(self.LINK_PATTERN, self.html))
