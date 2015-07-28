# -*- coding: utf-8 -*-

import array
import os
# import pycurl
import random
import re

from base64 import standard_b64decode

from Crypto.Cipher import AES
from Crypto.Util import Counter

from module.common.json_layer import json_loads, json_dumps
from module.plugins.internal.Hoster import Hoster
from module.utils import decode, fs_decode, fs_encode


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


class MegaCoNz(Hoster):
    __name__    = "MegaCoNz"
    __type__    = "hoster"
    __version__ = "0.31"
    __status__  = "testing"

    __pattern__ = r'(https?://(?:www\.)?mega(\.co)?\.nz/|mega:|chrome:.+?)#(?P<TYPE>N|)!(?P<ID>[\w^_]+)!(?P<KEY>[\w,-]+)'

    __description__ = """Mega.co.nz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "ranan@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    API_URL     = "https://eu.api.mega.co.nz/cs"
    FILE_SUFFIX = ".crypted"


    def b64_decode(self, data):
        data = data.replace("-", "+").replace("_", "/")
        return standard_b64decode(data + '=' * (-len(data) % 4))


    def get_cipher_key(self, key):
        """
        Construct the cipher key from the given data
        """
        a = array.array("I", self.b64_decode(key))

        k        = array.array("I", (a[0] ^ a[4], a[1] ^ a[5], a[2] ^ a[6], a[3] ^ a[7]))
        iv       = a[4:6] + array.array("I", (0, 0))
        meta_mac = a[6:8]

        return k, iv, meta_mac


    def api_response(self, **kwargs):
        """
        Dispatch a call to the api, see https://mega.co.nz/#developers
        """
        #: Generate a session id, no idea where to obtain elsewhere
        uid = random.randint(10 << 9, 10 ** 10)

        res = self.load(self.API_URL, get={'id': uid}, post=json_dumps([kwargs]))
        self.log_debug("Api Response: " + res)
        return json_loads(res)


    def decrypt_attr(self, data, key):
        k, iv, meta_mac = self.get_cipher_key(key)
        cbc             = AES.new(k, AES.MODE_CBC, "\0" * 16)
        attr            = decode(cbc.decrypt(self.b64_decode(data)))

        self.log_debug("Decrypted Attr: %s" % attr)
        if not attr.startswith("MEGA"):
            self.fail(_("Decryption failed"))

        #: Data is padded, 0-bytes must be stripped
        return json_loads(re.search(r'{.+?}', attr).group(0))


    def decrypt_file(self, key):
        """
        Decrypts the file at last_download`
        """
        #: Upper 64 bit of counter start
        n = self.b64_decode(key)[16:24]

        #: Convert counter to long and shift bytes
        k, iv, meta_mac = self.get_cipher_key(key)
        ctr             = Counter.new(128, initial_value=long(n.encode("hex"), 16) << 64)
        cipher          = AES.new(k, AES.MODE_CTR, counter=ctr)

        self.pyfile.setStatus("decrypting")
        self.pyfile.setProgress(0)

        file_crypted   = fs_encode(self.last_download)
        file_decrypted = file_crypted.rsplit(self.FILE_SUFFIX)[0]

        try:
            f  = open(file_crypted, "rb")
            df = open(file_decrypted, "wb")

        except IOError, e:
            self.fail(e)

        chunk_size = 2 ** 15  #: Buffer size, 32k
        # file_mac   = [0, 0, 0, 0]  # calculate CBC-MAC for checksum

        chunks = os.path.getsize(file_crypted) / chunk_size + 1
        for i in xrange(chunks):
            buf = f.read(chunk_size)
            if not buf:
                break

            chunk = cipher.decrypt(buf)
            df.write(chunk)

            self.pyfile.setProgress(int((100.0 / chunks) * i))

            # chunk_mac = [iv[0], iv[1], iv[0], iv[1]]
            # for i in xrange(0, chunk_size, 16):
                # block = chunk[i:i+16]
                # if len(block) % 16:
                    # block += '=' * (16 - (len(block) % 16))
                # block = array.array("I", block)

                # chunk_mac = [chunk_mac[0] ^ a_[0], chunk_mac[1] ^ block[1], chunk_mac[2] ^ block[2], chunk_mac[3] ^ block[3]]
                # chunk_mac = aes_cbc_encrypt_a32(chunk_mac, k)

            # file_mac = [file_mac[0] ^ chunk_mac[0], file_mac[1] ^ chunk_mac[1], file_mac[2] ^ chunk_mac[2], file_mac[3] ^ chunk_mac[3]]
            # file_mac = aes_cbc_encrypt_a32(file_mac, k)

        self.pyfile.setProgress(100)

        f.close()
        df.close()

        # if file_mac[0] ^ file_mac[1], file_mac[2] ^ file_mac[3] is not meta_mac:
            # os.remove(file_decrypted)
            # self.fail(_("Checksum mismatch"))

        os.remove(file_crypted)
        self.last_download = fs_decode(file_decrypted)


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


    def process(self, pyfile):
        pattern = re.match(self.__pattern__, pyfile.url).groupdict()
        id      = pattern['ID']
        key     = pattern['KEY']
        public  = pattern['TYPE'] == ""

        self.log_debug("ID: %s" % id, "Key: %s" % key, "Type: %s" % ("public" if public else "node"))

        #: G is for requesting a download url
        #: This is similar to the calls in the mega js app, documentation is very bad
        if public:
            mega = self.api_response(a="g", g=1, p=id, ssl=1)[0]
        else:
            mega = self.api_response(a="g", g=1, n=id, ssl=1)[0]

        if isinstance(mega, int):
            self.check_error(mega)
        elif "e" in mega:
            self.check_error(mega['e'])

        attr = self.decrypt_attr(mega['at'], key)

        pyfile.name = attr['n'] + self.FILE_SUFFIX
        pyfile.size = mega['s']

        # self.req.http.c.setopt(pycurl.SSL_CIPHER_LIST, "RC4-MD5:DEFAULT")

        self.download(mega['g'])

        self.decrypt_file(key)

        #: Everything is finished and final name can be set
        pyfile.name = attr['n']
