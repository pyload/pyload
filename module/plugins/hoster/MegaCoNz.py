# -*- coding: utf-8 -*-

import base64
import os
import random
import re
import struct

import Crypto.Cipher.AES
import Crypto.Util.Counter

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.misc import decode, encode, exists, fsjoin, json


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


class MegaCrypto(object):
    @staticmethod
    def base64_decode(data):
        data += '=' * (-len(data) % 4)  #: Add padding, we need a string with a length multiple of 4
        return base64.b64decode(str(data), "-_")


    @staticmethod
    def base64_encode(data):
        return base64.b64encode(data, "-_")


    @staticmethod
    def a32_to_str(a):
        return struct.pack(">%dI" % len(a), *a)  #: big-endian, unsigned int


    @staticmethod
    def str_to_a32(s):
        s += '\0' * (-len(s) % 4)  # Add padding, we need a string with a length multiple of 4
        return struct.unpack(">%dI" % (len(s) / 4), s)  #: big-endian, unsigned int


    @staticmethod
    def base64_to_a32(s):
        return MegaCrypto.str_to_a32(MegaCrypto.base64_decode(s))

    @staticmethod
    def cbc_decrypt(data, key):
        cbc = Crypto.Cipher.AES.new(MegaCrypto.a32_to_str(key), Crypto.Cipher.AES.MODE_CBC, "\0" * 16)
        return cbc.decrypt(data)


    @staticmethod
    def cbc_encrypt(data, key):
        cbc = Crypto.Cipher.AES.new(MegaCrypto.a32_to_str(key), Crypto.Cipher.AES.MODE_CBC, "\0" * 16)
        return cbc.encrypt(data)


    @staticmethod
    def get_cipher_key(key):
        """
        Construct the cipher key from the given data
        """
        k        = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6], key[3] ^ key[7])
        iv       = key[4:6] + (0, 0)
        meta_mac = key[6:8]

        return k, iv, meta_mac


    @staticmethod
    def decrypt_attr(data, key):
        """
        Decrypt an encrypted attribute (usually 'a' or 'at' member of a node)
        """
        data = MegaCrypto.base64_decode(data)
        k, iv, meta_mac = MegaCrypto.get_cipher_key(key)
        attr = MegaCrypto.cbc_decrypt(data, k)

        #: Data is padded, 0-bytes must be stripped
        return json.loads(re.search(r'{.+?}', attr).group(0)) if attr[:6] == 'MEGA{"' else False


    @staticmethod
    def decrypt_key(data, key):
        """
        Decrypt an encrypted key ('k' member of a node)
        """
        data = MegaCrypto.base64_decode(data)
        return sum((MegaCrypto.str_to_a32(MegaCrypto.cbc_decrypt(data[_i:_i + 16], key))
                    for _i in xrange(0, len(data), 16)), ())


    @staticmethod
    def get_chunks(size):
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


    class Checksum(object):
        """
        interface for checking CBC-MAC checksum
        """
        def __init__(self, key):
            k, iv, meta_mac = MegaCrypto.get_cipher_key(key)
            self.hash = '\0' * 16
            self.key  = MegaCrypto.a32_to_str(k)
            self.iv   = MegaCrypto.a32_to_str(iv[0:2] * 2)
            self.AES  = Crypto.Cipher.AES.new(self.key, mode=Crypto.Cipher.AES.MODE_CBC, IV=self.hash)


        def update(self, chunk):
            cbc = Crypto.Cipher.AES.new(self.key, mode=Crypto.Cipher.AES.MODE_CBC, IV=self.iv)
            for j in xrange(0, len(chunk), 16):
                block = chunk[j:j + 16].ljust(16, '\0')
                hash  = cbc.encrypt(block)

            self.hash = self.AES.encrypt(hash)


        def digest(self):
            """
            Return the **binary** (non-printable) CBC-MAC of the message that has been authenticated so far.
            """
            d = MegaCrypto.str_to_a32(self.hash)
            return (d[0] ^ d[1], d[2] ^ d[3])


        def hexdigest(self):
            """
            Return the **printable** CBC-MAC of the message that has been authenticated so far.
            """
            return "".join(["%02x" % ord(x)
                      for x in MegaCrypto.a32_to_str(self.digest())])


        @staticmethod
        def new(key):
            return MegaCrypto.Checksum(key)


class MegaClient(object):
    API_URL     = "https://eu.api.mega.co.nz/cs"

    def __init__(self, plugin, node_id):
        self.plugin  = plugin
        self.node_id = node_id


    def api_response(self, **kwargs):
        """
        Dispatch a call to the api, see https://mega.co.nz/#developers
        """
        uid = random.randint(10 << 9, 10 ** 10)  #: Generate a session id, no idea where to obtain elsewhere

        try:
            res = self.plugin.load(self.API_URL,
                                   get={'id': uid, 'n': self.node_id},
                                   post=json.dumps([kwargs]))

        except BadHeader, e:
            if e.code == 500:
                self.plugin.retry(wait_time=60, reason=_("Server busy"))
            else:
                raise

        self.plugin.log_debug(_("Api Response: ") + res)
        return json.loads(res)


    def check_error(self, code):
        ecode = abs(code)

        if ecode in (9, 16, 21):
            self.plugin.offline()

        elif ecode in (3, 13, 17, 18, 19):
            self.plugin.temp_offline()

        elif ecode in (1, 4, 6, 10, 15, 21):
            self.plugin.retry(max_tries=5, wait_time=30, reason=_("Error code: [%s]") % -ecode)

        else:
            self.plugin.fail(_("Error code: [%s]") % -ecode)


class MegaCoNz(Hoster):
    __name__    = "MegaCoNz"
    __type__    = "hoster"
    __version__ = "0.46"
    __status__  = "testing"

    __pattern__ = r'(https?://(?:www\.)?mega(\.co)?\.nz/|mega:|chrome:.+?)#(?P<TYPE>N|)!(?P<ID>[\w^_]+)!(?P<KEY>[\w\-,=]+)(?:###n=(?P<OWNER>[\w^_]+))?'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Mega.co.nz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN",          "ranan@pyload.org"          ),
                       ("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de",      "nitzo2001[AT}yahoo[DOT]com")]


    FILE_SUFFIX = ".crypted"


    def decrypt_file(self, key):
        """
        Decrypts and verifies checksum to the file at 'last_download'
        """
        k, iv, meta_mac = MegaCrypto.get_cipher_key(key)
        ctr             = Crypto.Util.Counter.new(128, initial_value = ((iv[0] << 32) + iv[1]) << 64)
        cipher          = Crypto.Cipher.AES.new(MegaCrypto.a32_to_str(k), Crypto.Cipher.AES.MODE_CTR, counter=ctr)

        self.pyfile.setStatus("decrypting")
        self.pyfile.setProgress(0)

        file_crypted   = encode(self.last_download)
        file_decrypted = file_crypted.rsplit(self.FILE_SUFFIX)[0]

        try:
            f  = open(file_crypted, "rb")
            df = open(file_decrypted, "wb")

        except IOError, e:
            self.fail(e.message)

        encrypted_size = os.path.getsize(file_crypted)

        checksum_activated = self.config.get("activated", default=False, plugin="Checksum")
        check_checksum     = self.config.get("check_checksum", default=True, plugin="Checksum")

        cbc_mac = MegaCrypto.Checksum(key) if checksum_activated and check_checksum else None

        progress = 0
        for chunk_start, chunk_size in MegaCrypto.get_chunks(encrypted_size):
            buf = f.read(chunk_size)
            if not buf:
                break

            chunk = cipher.decrypt(buf)
            df.write(chunk)

            progress += chunk_size
            self.pyfile.setProgress(int((100.0 / encrypted_size) * progress))

            if checksum_activated and check_checksum:
                cbc_mac.update(chunk)

        self.pyfile.setProgress(100)

        f.close()
        df.close()

        self.log_info(_("File decrypted"))
        os.remove(file_crypted)

        if checksum_activated and check_checksum:
            file_mac = cbc_mac.digest()
            if file_mac == meta_mac:
                self.log_info(_('File integrity of "%s" verified by CBC-MAC checksum (%s)') %
                              (self.pyfile.name.rsplit(self.FILE_SUFFIX)[0], meta_mac))
            else:
                self.log_warning(_('CBC-MAC checksum for file "%s" does not match (%s != %s)') %
                                 (self.pyfile.name.rsplit(self.FILE_SUFFIX)[0], file_mac, meta_mac))
                self.checksum_failed(file_decrypted, _("Checksums do not match"))

        self.last_download = decode(file_decrypted)


    def checksum_failed(self, local_file, msg):
        check_action = self.config.get("check_action", default="retry", plugin="Checksum")

        if check_action == "retry":
            max_tries = self.config.get("max_tries", default=2, plugin="Checksum")
            retry_action = self.config.get("retry_action", default="fail", plugin="Checksum")

            if all(_r < max_tries for _id, _r in self.retries.items()):
                os.remove(local_file)
                wait_time = self.config.get("wait_time", default=1, plugin="Checksum")
                self.retry(max_tries, wait_time, msg)

            elif retry_action == "nothing":
                return

        elif check_action == "nothing":
            return

        os.remove(local_file)
        self.fail(msg)


    def check_exists(self, name):
        """
        Because of Mega downloads a temporary encrypted file with the extension of '.crypted',
        pyLoad cannot correctly detect if the file exists before downloading.
        This function corrects this.

        Raises Skip() if file exists and 'skip_existing' configuration option is set to True.
        """
        if self.pyload.config.get("download", "skip_existing"):
            download_folder = self.pyload.config.get('general', 'download_folder')
            dest_file = fsjoin(download_folder,
                               self.pyfile.package().folder if self.pyload.config.get("general", "folder_per_package") else "",
                               name)
            if exists(dest_file):
                self.pyfile.name = name
                self.skip(_("File exists."))


    def process(self, pyfile):
        id      = self.info['pattern']['ID']
        key     = self.info['pattern']['KEY']
        public  = self.info['pattern']['TYPE'] == ""
        owner   = self.info['pattern']['OWNER']

        if not public and not owner:
            self.log_error(_("Missing owner in URL"))
            self.fail(_("Missing owner in URL"))

        self.log_debug(_("ID: %s") % id,
                       _("Key: %s") % key,
                       _("Type: %s") % ("public" if public else "node"),
                       _("Owner: %s") % owner)

        key = MegaCrypto.base64_to_a32(key)
        if len(key) != 8:
            self.log_error(_("Invalid key length"))
            self.fail(_("Invalid key length"))

        mega = MegaClient(self, self.info['pattern']['OWNER'] or self.info['pattern']['ID'])

        #: G is for requesting a download url
        #: This is similar to the calls in the mega js app, documentation is very bad
        if public:
            res = mega.api_response(a="g", g=1, p=id, ssl=1)
        else:
            res = mega.api_response(a="g", g=1, n=id, ssl=1)

        if isinstance(res, int):
            mega.check_error(res)
        elif isinstance(res, list):
            res = res[0]
            if "e" in res:
                mega.check_error(res['e'])

        attr = MegaCrypto.decrypt_attr(res['at'], key)
        if not attr:
            self.fail(_("Decryption failed"))

        self.log_debug(_("Decrypted Attr: %s") % decode(attr))

        name = attr['n']

        self.check_exists(name)

        pyfile.name = name + self.FILE_SUFFIX
        pyfile.size = res['s']

        time_left = res.get('tl', 0)
        if time_left:
            self.log_warning(_("Free download limit reached"))
            self.retry(wait=time_left, msg=_("Free download limit reached"))

        # self.req.http.c.setopt(pycurl.SSL_CIPHER_LIST, "RC4-MD5:DEFAULT")

        self.download(res['g'])

        self.decrypt_file(key)

        #: Everything is finished and final name can be set
        pyfile.name = name
