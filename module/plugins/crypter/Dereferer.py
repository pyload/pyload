# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class Dereferer(SimpleCrypter):
    __name__    = "Dereferer"
    __type__    = "crypter"
    __version__ = "0.13"

    __pattern__ = r'https?://(?:www\.)?(?:\w+\.)*?(?P<DOMAIN>(?:[\d.]+|[\w\-]{3,}(?:\.[a-zA-Z]{2,}){1,2})(?:\:\d+)?)/.*?(?P<LINK>(?:ht|f)tps?://.+)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Crypter for dereferers"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None
    HOSTER_NAME   = None


    def _log(self, type, args):
        msg = " | ".join(str(a).strip() for a in args if a)
        logger = getattr(self.log, type)
        logger("%s: %s: %s" % (self.__name__, self.HOSTER_NAME, msg or _("%s MARK" % type.upper())))


    def init(self):
        super(Dereferer, self).init()

        self.__pattern__ = self.core.pluginManager.crypterPlugins[self.__name__]['pattern']  #@TODO: Recheck in 0.4.10

        self.HOSTER_DOMAIN = re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        self.HOSTER_NAME   = "".join(part.capitalize() for part in re.split(r'(\.|\d+)', self.HOSTER_DOMAIN) if part != '.')


    def getLinks(self):
        return [re.match(self.__pattern__, pyfile.url).group('LINK').strip()]
