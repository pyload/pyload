# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class TinyurlCom(SimpleCrypter):
    __name__    = "TinyurlCom"
    __type__    = "crypter"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(preview\.)?tinyurl\.com/[\w-]+'

    __description__ = """Tinyurl.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(r'preview\.', r'')]

    OFFLINE_PATTERN = r">Error: Unable to find site's URL to redirect to"


getInfo = create_getInfo(TinyurlCom)
