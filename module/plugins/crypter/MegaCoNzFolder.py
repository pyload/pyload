# -*- coding: utf-8 -*-

from ..hoster.MegaCoNz import MegaClient, MegaCrypto
from ..internal.Crypter import Crypter


class MegaCoNzFolder(Crypter):
    __name__ = "MegaCoNzFolder"
    __type__ = "crypter"
    __version__ = "0.21"
    __status__ = "testing"

    __pattern__ = r'(https?://(?:www\.)?mega(\.co)?\.nz/|mega:|chrome:.+?)#F!(?P<ID>[\w^_]+)!(?P<KEY>[\w,\-=]+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """Mega.co.nz folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def decrypt(self, pyfile):
        id = self.info['pattern']['ID']
        master_key = self.info['pattern']['KEY']

        self.log_debug(
            "ID: %s" % id,
            "Key: %s" % master_key,
            "Type: public folder")

        master_key = MegaCrypto.base64_to_a32(master_key)

        mega = MegaClient(self, id)

        #: F is for requesting folder listing (kind like a `ls` command)
        res = mega.api_response(a="f", c=1, r=1, ca=1, ssl=1)

        if isinstance(res, int):
            mega.check_error(res)
        elif 'e' in res:
            mega.check_error(res['e'])

        get_node_key = lambda k: MegaCrypto.base64_encode(
            MegaCrypto.a32_to_str(MegaCrypto.decrypt_key(k, master_key)))

        self.links = [_("https://mega.co.nz/#N!%s!%s###n=%s") %
                      (_f['h'],
                       get_node_key(_f['k'][_f['k'].index(':') + 1:]),
                       id)
                      for _f in res['f']
                      if _f['t'] == 0 and ':' in _f['k']]
