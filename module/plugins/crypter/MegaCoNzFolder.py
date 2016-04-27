# -*- coding: utf-8 -*-

import base64
import random
import re
import struct

import Crypto.Cipher.AES

from module.plugins.internal.Crypter import Crypter
from module.plugins.internal.misc import decode, json


############################ General errors ###################################
# EINTERNAL            (-1): An internal error has occurred. Please submit a bug report, detailing the exact circumstances in which this error occurred
# EARGS                (-2): You have passed invalid arguments to this command
# EAGAIN               (-3): (always at the request level) A temporary congestion or server malfunction prevented your request from being processed. No data was altered. Retry. Retries must be spaced with exponential backoff
# ERATELIMIT           (-4): You have exceeded your command weight per time quota. Please wait a few seconds, then try again (this should never happen in sane real-life applications)
#
############################ Upload errors ####################################
# EFAILED              (-5): The upload failed. Please restart it from scratch
# ETOOMANY             (-6): Too many concurrent IP addresses are accessing this upload target URL
# ERANGE               (-7): The upload file packet is out of range or not starting and ending on a chunk boundary
# EEXPIRED             (-8): The upload target URL you are trying to access has expired. Please request a fresh one
#
############################ Stream/System errors #############################
# ENOENT               (-9): Object (typically, node or user) not found
# ECIRCULAR           (-10): Circular linkage attempted
# EACCESS             (-11): Access violation (e.g., trying to write to a read-only share)
# EEXIST              (-12): Trying to create an object that already exists
# EINCOMPLETE         (-13): Trying to access an incomplete resource
# EKEY                (-14): A decryption operation failed (never returned by the API)
# ESID                (-15): Invalid or expired user session, please relogin
# EBLOCKED            (-16): User blocked
# EOVERQUOTA          (-17): Request over quota
# ETEMPUNAVAIL        (-18): Resource temporarily not available, please try again later
# ETOOMANYCONNECTIONS (-19): Too many connections on this resource
# EWRITE              (-20): Write failed
# EREAD               (-21): Read failed
# EAPPKEY             (-22): Invalid application key; request not processed


class MegaCoNzFolder(Crypter):
    __name__    = "MegaCoNzFolder"
    __type__    = "crypter"
    __version__ = "0.15"
    __status__  = "testing"

    __pattern__ = r'(https?://(?:www\.)?mega(\.co)?\.nz/|mega:|chrome:.+?)#F!(?P<ID>[\w^_]+)!(?P<KEY>[\w,\-=]+)'
    __config__  = [("activated"         , "bool"          , "Activated"                       , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available", True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"  , "Default")]

    __description__ = """Mega.co.nz folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de",      "nitzo2001[AT]yahoo[DOT]com")]


    API_URL     = "https://eu.api.mega.co.nz/cs"


    def base64_decode(self, data):
        data += '=' * (-len(data) % 4)
        return base64.b64decode(str(data), "-_")


    def base64_encode(self, data):
        return base64.b64encode(data, "-_")


    def a32_to_str(self, a):
        return struct.pack(">%dI" % len(a), *a)  #: big-endian, unsigned int


    def str_to_a32(self, s):
        s += '\0' * (-len(s) % 4)  # Add padding, we need a string with a length multiple of 4
        return struct.unpack(">%dI" % (len(s) / 4), s)  #: big-endian, unsigned int


    def base64_to_a32(self, s):
        return self.str_to_a32(self.base64_decode(s))


    def cbc_decrypt(self, data, key):
        cbc = Crypto.Cipher.AES.new(self.a32_to_str(key), Crypto.Cipher.AES.MODE_CBC, "\0" * 16)
        return cbc.decrypt(data)


    def decrypt_key(self, a, key):
        a = self.base64_decode(a)
        k = sum((self.str_to_a32(self.cbc_decrypt(a[_i:_i + 16], key))
                    for _i in xrange(0, len(a), 16)), ())

        self.log_debug("Decrypted Key: %s" % decode(k))

        return k


    def api_response(self, **kwargs):
        """
        Dispatch a call to the api, see https://mega.co.nz/#developers
        """
        uid = random.randint(10 << 9, 10 ** 10)  #: Generate a session id, no idea where to obtain elsewhere

        res = self.load(self.API_URL,
                        get={'id': uid,
                             'n' : self.info['pattern']['ID']},
                        post=json.dumps([kwargs]))

        self.log_debug("Api Response: " + res)

        return json.loads(res)


    def check_error(self, code):
        ecode = abs(code)

        if ecode in (9, 16, 21):
            self.offline()

        elif ecode in (3, 13, 17, 18, 19):
            self.temp_offline()

        elif ecode in (1, 4, 6, 10, 15, 21):
            self.retry(5, 30, _("Error code: [%s]") % -ecode)

        else:
            self.fail(_("Error code: [%s]") % -ecode)


    def decrypt(self, pyfile):
        id         = self.info['pattern']['ID']
        master_key = self.info['pattern']['KEY']

        self.log_debug("ID: %s" % id, "Key: %s" % master_key, "Type: public folder")

        master_key =  self.base64_to_a32(master_key)

        #: F is for requesting folder listing (kind like a `ls` command)
        mega = self.api_response(a="f", c=1, r=1, ca=1, ssl=1)[0]

        if isinstance(mega, int):
            self.check_error(mega)
        elif "e" in mega:
            self.check_error(mega['e'])

        get_node_key = lambda k: self.base64_encode(self.a32_to_str(self.decrypt_key(k, master_key)))

        self.links = [_("https://mega.co.nz/#N!%s!%s###n=%s") %
                      (_f['h'],
                       get_node_key(_f['k'][_f['k'].index(':') + 1:]),
                       id)
                      for _f in mega['f']
                      if _f['t'] == 0 and ':' in _f['k']]
