# -*- coding: utf-8 -*-

import base64
import os
import random
import re
import struct

import Crypto.Cipher.AES
import Crypto.Util.Counter
# import pycurl

from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.misc import decode, encode, json


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
    __version__ = "0.40"
    __status__  = "testing"

    __pattern__ = r'(https?://(?:www\.)?mega(\.co)?\.nz/|mega:|chrome:.+?)#(?P<TYPE>N|)!(?P<ID>[\w^_]+)!(?P<KEY>[\w\-,=]+)(?:###n=(?P<OWNER>[\w^_]+))?'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Mega.co.nz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN",          "ranan@pyload.org"          ),
                       ("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de",      "nitzo2001[AT}yahoo[DOT]com")]


    API_URL     = "https://eu.api.mega.co.nz/cs"
    FILE_SUFFIX = ".crypted"


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


    def get_cipher_key(self, key):
        """
        Construct the cipher key from the given data
        """
        k        = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6], key[3] ^ key[7])
        iv       = key[4:6] + (0, 0)
        meta_mac = key[6:8]

        return k, iv, meta_mac


    def decrypt_attr(self, data, key):
        k, iv, meta_mac = self.get_cipher_key(key)
        cbc = Crypto.Cipher.AES.new(self.a32_to_str(k), Crypto.Cipher.AES.MODE_CBC, "\0" * 16)
        attr = cbc.decrypt(self.base64_decode(data))

        if not attr.startswith("MEGA"):
            self.fail(_("Decryption failed"))

        self.log_debug("Decrypted Attr: %s" % decode(attr))

        #: Data is padded, 0-bytes must be stripped
        return json.loads(re.search(r'{.+?}', attr).group(0))


    def api_response(self, **kwargs):
        """
        Dispatch a call to the api, see https://mega.co.nz/#developers
        """
        uid = random.randint(10 << 9, 10 ** 10)  #: Generate a session id, no idea where to obtain elsewhere

        res = self.load(self.API_URL,
                        get={'id': uid,
                             'n' : self.info['pattern']['OWNER'] or self.info['pattern']['ID']},
                        post=json.dumps([kwargs]))

        self.log_debug("Api Response: " + res)
        return json.loads(res)


    def get_chunks(self, size):
        """
        Calculate chunks for a given encrypted file size
        """
        chunk_start = 0
        chunk_size  = 0x20000

        while chunk_start + chunk_size < size:
            yield (chunk_start, chunk_size)
            chunk_start += chunk_size
            if chunk_size < 0x100000:
                chunk_size += 0x20000

        if chunk_start < size:
            yield (chunk_start, size - chunk_start)


    def decrypt_file(self, key):
        """
        Decrypts and verifies checksum to the file at last_download`
        """
        k, iv, meta_mac = self.get_cipher_key(key)
        ctr             = Crypto.Util.Counter.new(128, initial_value = ((iv[0] << 32) + iv[1]) << 64)
        cipher          = Crypto.Cipher.AES.new(self.a32_to_str(k), Crypto.Cipher.AES.MODE_CTR, counter=ctr)

        self.pyfile.setStatus("decrypting")
        self.pyfile.setProgress(0)

        file_crypted   = encode(self.last_download)
        file_decrypted = file_crypted.rsplit(self.FILE_SUFFIX)[0]

        try:
            f  = open(file_crypted, "rb")
            df = open(file_decrypted, "wb")

        except IOError, e:
            self.fail(e.message)

        file_mac = [0, 0, 0, 0]  # calculate CBC-MAC for checksum

        crypted_size = os.path.getsize(file_crypted)

        checksum_activated = self.config.get("activated", default=False, plugin="Checksum")
        check_checksum = self.config.get("check_checksum", default=True, plugin="Checksum")

        progress = 0
        for chunk_start, chunk_size in self.get_chunks(crypted_size):
            buf = f.read(chunk_size)
            if not buf:
                break

            chunk = cipher.decrypt(buf)
            df.write(chunk)

            progress += chunk_size
            self.pyfile.setProgress(int((100.0 / crypted_size) * progress))

            if checksum_activated and check_checksum:
                chunk_mac = [iv[0], iv[1], iv[0], iv[1]]
                for j in xrange(0, len(chunk), 16):
                    block = chunk[j:j + 16]
                    block += '\0' * (-len(block) % 16)
                    block = self.str_to_a32(block)
                    chunk_mac = [chunk_mac[0] ^ block[0], chunk_mac[1] ^ block[1], chunk_mac[2] ^ block[2],
                                 chunk_mac[3] ^ block[3]]

                    cbc = Crypto.Cipher.AES.new(self.a32_to_str(k), Crypto.Cipher.AES.MODE_CBC, "\0" * 16)
                    chunk_mac = self.str_to_a32(cbc.encrypt(self.a32_to_str(chunk_mac)))

                file_mac = [file_mac[0] ^ chunk_mac[0], file_mac[1] ^ chunk_mac[1], file_mac[2] ^ chunk_mac[2],
                            file_mac[3] ^ chunk_mac[3]]
                cbc = Crypto.Cipher.AES.new(self.a32_to_str(k), Crypto.Cipher.AES.MODE_CBC, "\0" * 16)
                file_mac = self.str_to_a32(cbc.encrypt(self.a32_to_str(file_mac)))

        self.pyfile.setProgress(100)

        f.close()
        df.close()

        self.log_info(_("File decrypted"))
        self.remove(file_crypted, trash=False)

        if checksum_activated and check_checksum:
            file_mac = (file_mac[0] ^ file_mac[1], file_mac[2] ^ file_mac[3])
            if file_mac == meta_mac:
                self.log_info(_('File integrity of "%s" verified by CBC-MAC checksum (%s)') %
                              (file_decrypted, meta_mac))
            else:
                self.log_warning(_('CBC-MAC checksum for file "%s" does not match (%s != %s)') %
                                 (self.pyfile.name, file_mac, meta_mac))
                self.checksum_failed(file_decrypted, _("Checksums do not match"))

        self.last_download = decode(file_decrypted)


    def checksum_failed(self, local_file, msg):
        check_action = self.config.get("check_action", default="retry", plugin="Checksum")
        if check_action == "retry":
            max_tries = self.config.get("max_tries", default=2, plugin="Checksum")
            retry_action = self.config.get("retry_action", default="fail", plugin="Checksum")
            if all(_r < max_tries for _id, _r in self.retries.items()):
                self.remove(local_file, trash=False)
                wait_time = self.config.get("wait_time", default=1, plugin="Checksum")
                self.retry(max_tries, wait_time, msg)

            elif retry_action == "nothing":
                return

        elif check_action == "nothing":
            return

        self.fail(msg)


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
        id      = self.info['pattern']['ID']
        key     = self.info['pattern']['KEY']
        public  = self.info['pattern']['TYPE'] == ""
        owner   = self.info['pattern']['OWNER']

        if not public and not owner:
            self.log_error(_("Missing owner in URL"))
            self.fail(_("Missing owner in URL"))

        self.log_debug("ID: %s" % id, "Key: %s" % key, "Type: %s" % ("public" if public else "node"), "Owner: %s" % owner)

        key = self.base64_to_a32(key)

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
