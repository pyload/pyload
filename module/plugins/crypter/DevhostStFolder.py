#Testlink: http://d-h.st/users/shine/?fld_id=37263#files

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DevhostStFolder(SimpleCrypter):
    __name__ = "DevhostStFolder"
    __type__ = "crypter"
    __version__ = "0.01"
    __description__ = """d-h.st decrypter plugin"""
    __pattern__ = r"https?://(?:www\.)?d-h.st/users/.*"
    __author_name_ = "zapp-brannigan"
    __author_mail_ = "fuerst.reinje@web.de"

    LINK_PATTERN = r'width: 530px;"><a href="(.+)">'

    def getLinks(self):
        return ['http://d-h.st%s' % link for link in re.findall(self.LINK_PATTERN, self.html)]
