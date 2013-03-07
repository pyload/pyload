# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter

class SpeedLoadOrgFolder(SimpleCrypter):
    __name__ = "SpeedLoadOrgFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?speedload\.org/(\d+~f$|folder/\d+/)"
    __version__ = "0.2"
    __description__ = """Speedload Crypter Plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    LINK_PATTERN = r'<div class="link"><a href="(http://speedload.org/\w+)"'
