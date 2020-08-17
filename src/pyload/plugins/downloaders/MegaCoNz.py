# -*- coding: utf-8 -*-

import base64
import json
import os
import random
import re
import struct

import Cryptodome.Cipher.AES
import Cryptodome.Util.Counter

from pyload.core.network.http.exceptions import BadHeader
from pyload.core.utils.old import decode

from ..base.downloader import BaseDownloader
from ..helpers import exists

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
# ESSL                (-23): SSL verification failed


class MegaCrypto:
    @staticmethod
    def base64_decode(data):
        #: Add padding, we need a string with a length multiple of 4
        data += "=" * (-len(data) % 4)
        return base64.b64decode(str(data), "-_")

    @staticmethod
    def base64_encode(data):
        return base64.b64encode(data, "-_")

    @staticmethod
    def a32_to_str(a):
        return struct.pack(">{}I".format(len(a)), *a)  #: big-endian, unsigned int)

    @staticmethod
    def str_to_a32(s):
        # Add padding, we need a string with a length multiple of 4
        s += "\0" * (-len(s) % 4)
        #: big-endian, unsigned int
        return struct.unpack(">{}I".format(len(s) // 4), s)

    @staticmethod
    def a32_to_base64(a):
        return MegaCrypto.base64_encode(MegaCrypto.a32_to_str(a))

    @staticmethod
    def base64_to_a32(s):
        return MegaCrypto.str_to_a32(MegaCrypto.base64_decode(s))

    @staticmethod
    def cbc_decrypt(data, key):
        cbc = Cryptodome.Cipher.AES.new(
            MegaCrypto.a32_to_str(key), Cryptodome.Cipher.AES.MODE_CBC, "\0" * 16
        )
        return cbc.decrypt(data)

    @staticmethod
    def cbc_encrypt(data, key):
        cbc = Cryptodome.Cipher.AES.new(
            MegaCrypto.a32_to_str(key), Cryptodome.Cipher.AES.MODE_CBC, "\0" * 16
        )
        return cbc.encrypt(data)

    @staticmethod
    def get_cipher_key(key):
        """
        Construct the cipher key from the given data.
        """
        k = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6], key[3] ^ key[7])
        iv = key[4:6] + (0, 0)
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
        return (
            json.loads(re.search(r"{.+}", attr).group(0))
            if attr[:6] == 'MEGA{"'
            else False
        )

    @staticmethod
    def decrypt_key(data, key):
        """
        Decrypt an encrypted key ('k' member of a node)
        """
        data = MegaCrypto.base64_decode(data)
        return sum(
            (
                MegaCrypto.str_to_a32(MegaCrypto.cbc_decrypt(data[i : i + 16], key))
                for i in range(0, len(data), 16)
            ),
            (),
        )

    @staticmethod
    def encrypt_key(data, key):
        """
        Encrypt a decrypted key.
        """
        data = MegaCrypto.base64_decode(data)
        return sum(
            (
                MegaCrypto.str_to_a32(MegaCrypto.cbc_encrypt(data[i : i + 16], key))
                for i in range(0, len(data), 16)
            ),
            (),
        )

    @staticmethod
    def get_chunks(size):
        """
        Calculate chunks for a given encrypted file size.
        """
        chunk_start = 0
        chunk_size = 0x20000

        while chunk_start + chunk_size < size:
            yield (chunk_start, chunk_size)
            chunk_start += chunk_size
            if chunk_size < 0x100000:
                chunk_size += 0x20000

        if chunk_start < size:
            yield (chunk_start, size - chunk_start)

    class Checksum:
        """
        interface for checking CBC-MAC checksum.
        """

        def __init__(self, key):
            k, iv, meta_mac = MegaCrypto.get_cipher_key(key)
            self.hash = "\0" * 16
            self.key = MegaCrypto.a32_to_str(k)
            self.iv = MegaCrypto.a32_to_str(iv[0:2] * 2)
            self.AES = Cryptodome.Cipher.AES.new(
                self.key, mode=Cryptodome.Cipher.AES.MODE_CBC, IV=self.hash
            )

        def update(self, chunk):
            cbc = Cryptodome.Cipher.AES.new(
                self.key, mode=Cryptodome.Cipher.AES.MODE_CBC, IV=self.iv
            )
            for j in range(0, len(chunk), 16):
                block = chunk[j : j + 16].ljust(16, "\0")
                hash = cbc.encrypt(block)

            self.hash = self.AES.encrypt(hash)

        def digest(self):
            """
            Return the **binary** (non-printable) CBC-MAC of the message that has been
            authenticated so far.
            """
            d = MegaCrypto.str_to_a32(self.hash)
            return (d[0] ^ d[1], d[2] ^ d[3])

        def hexdigest(self):
            """
            Return the **printable** CBC-MAC of the message that has been authenticated
            so far.
            """
            return "".join(
                "{:2x}".format(ord(x)) for x in MegaCrypto.a32_to_str(self.digest())
            )

        @staticmethod
        def new(key):
            return MegaCrypto.Checksum(key)


class MegaClient:
    API_URL = "https://eu.api.mega.co.nz/cs"

    def __init__(self, plugin, node_id):
        self.plugin = plugin
        self._ = plugin._
        self.node_id = node_id

    def api_response(self, **kwargs):
        """
        Dispatch a call to the api, see https://mega.co.nz/#developers.
        """
        uid = random.randint(
            10 << 9, 10 ** 10
        )  #: : Generate a session id, no idea where to obtain elsewhere
        get_params = {"id": uid}

        if self.node_id:
            get_params["n"] = self.node_id

        if hasattr(self.plugin, "account"):
            if self.plugin.account:
                mega_session_id = self.plugin.account.info["data"].get(
                    "mega_session_id", None
                )

            else:
                mega_session_id = None

        else:
            mega_session_id = self.plugin.info["data"].get("mega_session_id", None)

        if mega_session_id:
            get_params["sid"] = mega_session_id

        try:
            res = self.plugin.load(
                self.API_URL, get=get_params, post=json.dumps([kwargs])
            )

        except BadHeader as exc:
            if exc.code == 500:
                self.plugin.retry(wait_time=60, reason=self._("Server busy"))
            else:
                raise

        self.plugin.log_debug("Api Response: " + res)

        res = json.loads(res)
        if isinstance(res, list):
            res = res[0]

        return res

    def check_error(self, code):
        ecode = abs(code)

        if ecode in (9, 16, 21):
            self.plugin.offline()

        elif ecode in (3, 13, 17, 18, 19):
            self.plugin.temp_offline()

        elif ecode in (1, 4, 6, 10, 15, 21):
            self.plugin.retry(
                max_tries=5,
                wait_time=30,
                reason=self._("Error code: [{}]").format(-ecode),
            )

        else:
            self.plugin.fail(self._("Error code: [{}]").format(-ecode))


class MegaCoNz(BaseDownloader):
    __name__ = "MegaCoNz"
    __type__ = "downloader"
    __version__ = "0.52"
    __status__ = "testing"

    __pattern__ = r"(https?://(?:www\.)?mega(\.co)?\.nz/|mega:|chrome:.+?)#(?P<TYPE>N|)!(?P<ID>[\w^_]+)!(?P<KEY>[\w\-,=]+)(?:###n=(?P<OWNER>[\w^_]+))?"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Mega.co.nz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "ranan@pyload.net"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT}yahoo[DOT]com"),
    ]

    FILE_SUFFIX = ".crypted"

    def decrypt_file(self, key):
        """
        Decrypts and verifies checksum to the file at 'last_download'.
        """
        k, iv, meta_mac = MegaCrypto.get_cipher_key(key)
        ctr = Cryptodome.Util.Counter.new(
            128, initial_value=((iv[0] << 32) + iv[1]) << 64
        )
        cipher = Cryptodome.Cipher.AES.new(
            MegaCrypto.a32_to_str(k), Cryptodome.Cipher.AES.MODE_CTR, counter=ctr
        )

        self.pyfile.set_status("decrypting")
        self.pyfile.set_progress(0)

        file_crypted = os.fsdecode(self.last_download)
        file_decrypted = file_crypted.rsplit(self.FILE_SUFFIX)[0]

        try:
            f = open(file_crypted, mode="rb")
            df = open(file_decrypted, mode="wb")

        except IOError as exc:
            self.fail(exc)

        encrypted_size = os.path.getsize(file_crypted)

        checksum_activated = self.config.get(
            "enabled", default=False, plugin="Checksum"
        )
        check_checksum = self.config.get(
            "check_checksum", default=True, plugin="Checksum"
        )

        cbc_mac = (
            MegaCrypto.Checksum(key) if checksum_activated and check_checksum else None
        )

        progress = 0
        for chunk_start, chunk_size in MegaCrypto.get_chunks(encrypted_size):
            buf = f.read(chunk_size)
            if not buf:
                break

            chunk = cipher.decrypt(buf)
            df.write(chunk)

            progress += chunk_size
            self.pyfile.set_progress((100 // encrypted_size) * progress)

            if checksum_activated and check_checksum:
                cbc_mac.update(chunk)

        self.pyfile.set_progress(100)

        f.close()
        df.close()

        self.log_info(self._("File decrypted"))
        os.remove(file_crypted)

        if checksum_activated and check_checksum:
            file_mac = cbc_mac.digest()
            if file_mac == meta_mac:
                self.log_info(
                    self._(
                        'File integrity of "{}" verified by CBC-MAC checksum ({})'
                    ).format(self.pyfile.name.rsplit(self.FILE_SUFFIX)[0], meta_mac)
                )
            else:
                self.log_warning(
                    self._(
                        'CBC-MAC checksum for file "{}" does not match ({} != {})'
                    ).format(
                        self.pyfile.name.rsplit(self.FILE_SUFFIX)[0], file_mac, meta_mac
                    )
                )
                self.checksum_failed(file_decrypted, self._("Checksums do not match"))

        self.last_download = decode(file_decrypted)

    def checksum_failed(self, local_file, msg):
        check_action = self.config.get(
            "check_action", default="retry", plugin="Checksum"
        )

        if check_action == "retry":
            max_tries = self.config.get("max_tries", default=2, plugin="Checksum")
            retry_action = self.config.get(
                "retry_action", default="fail", plugin="Checksum"
            )

            if all(r < max_tries for _, r in self.retries.items()):
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
        Because of Mega downloads a temporary encrypted file with the extension of
        '.crypted', pyLoad cannot correctly detect if the file exists before
        downloading. This function corrects this.

        Raises Skip() if file exists and 'skip_existing' configuration option is
        set to True.
        """
        if self.pyload.config.get("download", "skip_existing"):
            storage_folder = self.pyload.config.get("general", "storage_folder")
            dest_file = os.path.join(
                storage_folder,
                self.pyfile.package().folder
                if self.pyload.config.get("general", "folder_per_package")
                else "",
                name,
            )
            if exists(dest_file):
                self.pyfile.name = name
                self.skip(self._("File exists."))

    def process(self, pyfile):
        id = self.info["pattern"]["ID"]
        key = self.info["pattern"]["KEY"]
        public = self.info["pattern"]["TYPE"] == ""
        owner = self.info["pattern"]["OWNER"]

        if not public and not owner:
            self.log_error(self._("Missing owner in URL"))
            self.fail(self._("Missing owner in URL"))

        self.log_debug(
            "ID: {}".format(id),
            self._("Key: {}").format(key),
            self._("Type: {}").format("public" if public else "node"),
            self._("Owner: {}").format(owner),
        )

        key = MegaCrypto.base64_to_a32(key)
        if len(key) != 8:
            self.log_error(self._("Invalid key length"))
            self.fail(self._("Invalid key length"))

        mega = MegaClient(
            self, self.info["pattern"]["OWNER"] or self.info["pattern"]["ID"]
        )

        #: G is for requesting a download url
        #: This is similar to the calls in the mega js app, documentation is very bad
        if public:
            res = mega.api_response(a="g", g=1, p=id, ssl=1)
        else:
            res = mega.api_response(a="g", g=1, n=id, ssl=1)

        if isinstance(res, int):
            mega.check_error(res)
        elif isinstance(res, dict) and "e" in res:
            mega.check_error(res["e"])

        attr = MegaCrypto.decrypt_attr(res["at"], key)
        if not attr:
            self.fail(self._("Decryption failed"))

        self.log_debug(f"Decrypted Attr: {decode(attr)}")

        name = attr["n"]

        self.check_exists(name)

        pyfile.name = name + self.FILE_SUFFIX
        pyfile.size = res["s"]

        time_left = res.get("tl", 0)
        if time_left:
            self.log_warning(self._("Free download limit reached"))
            self.retry(wait=time_left, msg=self._("Free download limit reached"))

        # self.req.http.c.setopt(pycurl.SSL_CIPHER_LIST, "RC4-MD5:DEFAULT")

        try:
            self.download(res["g"])

        except BadHeader as exc:
            if exc.code == 509:
                self.fail(self._("Bandwidth Limit Exceeded"))

            else:
                raise

        self.decrypt_file(key)

        #: Everything is finished and final name can be set
        pyfile.name = name
