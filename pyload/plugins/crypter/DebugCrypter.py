# -*- coding: utf-8 -*-

from random import randint
from time import sleep

from pyload.plugins.Crypter import Crypter

class DebugCrypter(Crypter):
    """ Generates link used by debug hoster to test the decrypt mechanism """

    __version__ = 0.1
    __pattern__ = r"^debug_crypter=(\d+)$"


    def decryptURL(self, url):

        m = self.pattern.search(url)
        n = int(m.group(1))

        sleep(randint(3, n if n > 2 else 3))

        return ["debug_hoster=%d" % i for i in range(n)]
