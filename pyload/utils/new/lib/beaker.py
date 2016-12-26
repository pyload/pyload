# -*- coding: utf-8 -*-
#
# Beaker legacy patch

from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import object

from beaker import *

if not hasattr(crypto.pbkdf2, "PBKDF2"):
    import binascii

    class PBKDF2(object):
        def __init__(self, passphrase, salt, iterations=1000):
            self.passphrase = passphrase
            self.salt = salt
            self.iterations = iterations

        def hexread(self, octets):
            return binascii.b2a_hex(
                crypto.pbkdf2.pbkdf2(
                    self.passphrase, self.salt, self.iterations, octets
                )
            )

    crypto.pbkdf2.PBKDF2 = PBKDF2
