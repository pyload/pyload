# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class FurLy(SimpleCrypter):
    __name__    = "FurLy"
    __type__    = "crypter"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?fur\.ly/(\d/)?\w+'

    __description__ = """Fur.ly decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [(r'fur\.ly/', r'fur\.ly/bar/')]

    LINK_PATTERN    = r'urls\[\d+\] = "(.+?)"'
    OFFLINE_PATTERN = r'var output;\s*var total'


getInfo = create_getInfo(FurLy)
