import base64
import json
import os
import random
import re
import struct
import threading
import time
from collections import deque
from queue import Empty, Queue

import pycurl
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pyload.core.network.exceptions import Abort
from pyload.core.network.http.exceptions import BadHeader
from pyload.core.utils import format, fs
from pyload.core.utils.convert import to_bytes, to_str
from pyload.core.utils.struct.lock import lock

from ..base.addon import threaded
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
# EGOINGOVERQUOTA     (-24): Not enough quota
# EMFAREQUIRED        (-26): Multi-factor authentication required
# EHASHCASHREQUIRED   (-27): HashCash challenge required


class OverQuotaError(RuntimeError):
    pass


class MegaCrypto:
    @staticmethod
    def base64_decode(data):
        data = to_bytes(data, "ascii")
        #: Add padding, we need a string with a length multiple of 4
        data += b"=" * (-len(data) % 4)
        return base64.b64decode(data, b"-_")

    @staticmethod
    def base64_encode(data):
        return to_str(base64.b64encode(data, b"-_"), "ascii").replace("=", "")

    @staticmethod
    def a32_to_bytes(a):
        return struct.pack(">{}I".format(len(a)), *a)  #: big-endian, unsigned int)

    @staticmethod
    def bytes_to_a32(s):
        # Add padding, we need a string with a length multiple of 4
        s += b"\0" * (-len(s) % 4)
        #: big-endian, unsigned int
        return struct.unpack(">{}I".format(len(s) // 4), s)

    @staticmethod
    def a32_to_base64(a):
        return MegaCrypto.base64_encode(MegaCrypto.a32_to_bytes(a))

    @staticmethod
    def base64_to_a32(s):
        return MegaCrypto.bytes_to_a32(MegaCrypto.base64_decode(s))

    @staticmethod
    def cbc_decrypt(data, key):
        cipher = Cipher(
            algorithms.AES(MegaCrypto.a32_to_bytes(key)),
            modes.CBC(b"\0" * 16),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()

    @staticmethod
    def cbc_encrypt(data, key):
        cipher = Cipher(
            algorithms.AES(MegaCrypto.a32_to_bytes(key)),
            modes.CBC(b"\0" * 16),
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()

    @staticmethod
    def ecb_decrypt(data, key):
        cipher = Cipher(
            algorithms.AES(MegaCrypto.a32_to_bytes(key)),
            modes.ECB(),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()

    @staticmethod
    def ecb_encrypt(data, key):
        cipher = Cipher(
            algorithms.AES(MegaCrypto.a32_to_bytes(key)),
            modes.ECB(),
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()

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
            json.loads(re.search(rb"{.+}", attr).group(0))
            if attr[:6] == b'MEGA{"'
            else False
        )

    @staticmethod
    def decrypt_key(data, key):
        """
        Decrypt an encrypted key ('k' member of a node)
        """
        data = MegaCrypto.base64_decode(data)
        return MegaCrypto.bytes_to_a32(MegaCrypto.ecb_decrypt(data, key))

    @staticmethod
    def encrypt_key(data, key):
        """
        Encrypt a decrypted key.
        """
        data = MegaCrypto.a32_to_bytes(data)
        return MegaCrypto.bytes_to_a32(MegaCrypto.ecb_encrypt(data, key))

    @staticmethod
    def get_chunks(size):
        """
        Calculate chunks for a given encrypted file size.
        """
        chunk_start = 0
        chunk_size = 0x20000

        while chunk_start + chunk_size < size:
            yield chunk_start, chunk_size
            chunk_start += chunk_size
            if chunk_size < 0x100000:
                chunk_size += 0x20000

        if chunk_start < size:
            yield chunk_start, size - chunk_start

    @staticmethod
    def solve_hashcash(challenge: str, easiness: int) -> str:
        """
        Compute proof-of-work Hashcash challenge.

        :param challenge: challenge from the X-Hashcash header value from the 402 response (4th part)
        :param easiness: easiness threshold - the lower, the harder to solve
        :return: Base64 URL-encoded prefix that satisfies the difficulty target
        """
        token = MegaCrypto.base64_decode(challenge)
        token += b"\0" * (-len(token) % 16)  # Add 0-padding to AES block size
        if len(token) != 48:
            raise ValueError("Invalid token value")

        buffer = bytearray(b'\0' * 4 + token * 0x40000)
        threshold = (((easiness & 63) << 1) + 1) << ((easiness >> 6) * 7 + 3)

        while True:
            # Increment the 4-byte nonce (little-endian)
            nonce = (int.from_bytes(buffer[:4], 'little') + 1) % (1 << 32)
            buffer[:4] = nonce.to_bytes(4, 'little')

            # Compute SHA-256 hash
            hasher = hashes.Hash(hashes.SHA256(), backend=default_backend())
            hasher.update(buffer)
            hash_digest = hasher.finalize()

            # Check first 4 bytes as big-endian uint32
            achieved_value = int.from_bytes(hash_digest[:4], 'big')
            if achieved_value <= threshold:
                # Return base64-encoded nonce
                return MegaCrypto.base64_encode(buffer[:4])

    class Checksum:
        """
        interface for checking CBC-MAC checksum.
        """

        def __init__(self, key):
            k, iv, meta_mac = MegaCrypto.get_cipher_key(key)
            self.hash = b"\0" * 16
            self.key = MegaCrypto.a32_to_bytes(k)
            self.iv = MegaCrypto.a32_to_bytes(iv[0:2] * 2)

            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(self.hash),
                backend=default_backend(),
            )
            self.AES = cipher.encryptor()

        def update(self, chunk):
            cipher = Cipher(
                algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend()
            )
            encryptor = cipher.encryptor()

            for j in range(0, len(chunk), 16):
                block = chunk[j:j + 16].ljust(16, b"\0")
                hash = encryptor.update(block)

            encryptor.finalize()

            self.hash = self.AES.update(hash)

        def digest(self):
            """
            Return the **binary** (non-printable) CBC-MAC of the message that has been
            authenticated so far.
            """
            d = MegaCrypto.bytes_to_a32(self.hash)
            return d[0] ^ d[1], d[2] ^ d[3]

        def hexdigest(self):
            """
            Return the **printable** CBC-MAC of the message that has been authenticated
            so far.
            """
            return MegaCrypto.a32_to_bytes(self.digest()).hex()

        @staticmethod
        def new(key):
            return MegaCrypto.Checksum(key)


class MegaClient:
    API_URL = "https://eu.api.mega.co.nz/cs"

    def __init__(self, plugin, node_id, tracking_id=True):
        self.plugin = plugin
        self._ = plugin._
        self.node_id = node_id
        self.tracking_id = random.randint(10 << 9, 10 ** 10) if tracking_id is True else tracking_id

    def api_request(self, **kwargs):
        """
        Dispatch a call to the api, see https://mega.co.nz/#developers.
        """
        get_params = {"id": self.tracking_id} if self.tracking_id else {}

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

        if self.tracking_id:
            self.tracking_id += 1  # increment on success

        self.plugin.log_debug("Api Response: " + res)

        res = json.loads(res)
        if isinstance(res, list):
            res = res[0]

        return res

    def check_error(self, code):
        ecode = abs(code)

        if ecode in (9, 16, 21):
            self.plugin.offline()

        elif ecode in (3, 13, 17, 18, 19, 24):
            self.plugin.temp_offline()

        elif ecode in (1, 4, 6, 10, 15):
            self.plugin.retry(
                max_tries=5,
                wait_time=30,
                reason=self._("Error code: [{}]").format(-ecode),
            )

        else:
            self.plugin.fail(self._("Error code: [{}]").format(-ecode))


class AggregatedDownload:
    """
    Aggregates metrics (speed, progress, size) from multiple worker browsers.
    Registered as master_browser.dl so the UI/main loop sees combined progress.
    """

    def __init__(self, total_size, master_browser=None, progress_notify=None):
        self.total_size = total_size
        self.master_browser = master_browser
        self.progress_notify = progress_notify
        self.abort = False
        self.code = 0
        self._last_progress = 0
        self.lock = threading.Lock()
        self._browsers = {}
        self._persisted_bytes = 0
        self._speed_samples = deque(maxlen=5)
        self._last_speed_sample_time = 0.0

    def set_persisted_bytes(self, persisted_bytes):
        with self.lock:
            self._persisted_bytes = max(0, persisted_bytes)

    def _live_arrived(self):
        return sum(
            (browser.dl.arrived if browser.dl else 0)
            for browser in self._browsers.values()
        )

    def register_browser(self):
        """Create and register the Browser for the current worker thread."""
        if self.master_browser is None:
            raise ValueError("master_browser must be set before registering workers")

        tid = threading.get_ident()
        with self.lock:
            browser = self._browsers.get(tid)
            if browser is None:
                browser = self.master_browser.__class__(
                    bucket=self.master_browser.bucket,
                    options=self.master_browser.options.copy(),
                )
                if self.master_browser.cj:
                    browser.set_cookie_jar(self.master_browser.cj)
                self._browsers[tid] = browser
            return browser

    def unregister_browser(self):
        """Remove the current worker thread's Browser from the registry."""
        tid = threading.get_ident()
        with self.lock:
            self._browsers.pop(tid, None)

    # @property
    # def abort(self):
    #     return self._abort
    #
    # @abort.setter
    # def abort(self, value):
    #     if value and not self._abort:
    #         self.abort_all()
    #     self._abort = value

    @property
    def size(self):
        return self.total_size

    @property
    @lock
    def arrived(self):
        """Sum of bytes arrived across live workers and persisted chunks."""
        return self._persisted_bytes + self._live_arrived()

    @property
    @lock
    def speed(self):
        """Average total speed across a small rolling window, sampled at least one second apart."""
        speeds = [
            browser.dl.speed
            for browser in self._browsers.values()
            if browser.dl
        ]
        live_speed = sum(speeds)

        now = time.monotonic()
        if now - self._last_speed_sample_time >= 1:
            self._speed_samples.append(live_speed)
            self._last_speed_sample_time = now

        return int(sum(self._speed_samples) / len(self._speed_samples))

    @property
    def percent(self):
        if not self.total_size:
            return 0
        return (self.arrived * 100) // self.total_size

    def update_progress(self):
        """Send progress callback if progress changed."""
        current = self.percent
        if current != self._last_progress and self.progress_notify:
            self._last_progress = current
            self.progress_notify(current)

    def abort_all(self):
        """Signal all workers to abort."""
        self.abort = True
        with self.lock:
            for browser in list(self._browsers.values()):
                if browser.dl:
                    browser.dl.abort = True


class MegaChunkedDownload:
    def __init__(self, plugin, url, filename, file_size, chunk_size_mb=None):
        self.plugin = plugin
        self.url = url
        self.filename = filename
        self.file_size = file_size
        self.chunk_size_mb = chunk_size_mb or plugin.config.get("chunk_size", 16)
        self.chunk_size = max(1, self.chunk_size_mb) * 1024 * 1024
        self.chunk_count = max(1, (self.file_size + self.chunk_size - 1) // self.chunk_size)  # Ceiling division
        self.chunks_info = []
        self.chunks_downloaded = {}
        self.aggregated_dl = None  # AggregatedDownload instance
        self.stop_requests = False
        self.exception_holder = None
        self._build_chunks_info()

    def _build_chunks_info(self):
        for i in range(self.chunk_count):
            start_pos = i * self.chunk_size
            end_pos = ((i + 1) * self.chunk_size - 1) if i < self.chunk_count - 1 else (self.file_size - 1)
            self.chunks_info.append((i, start_pos, end_pos))

    def get_chunk_metadata_path(self, file_path=None):
        return (file_path or self.filename) + self.plugin.CHUNK_METADATA_SUFFIX

    @property
    def pyload(self):
        return self.plugin.pyload

    def save_chunk_metadata(self, file_path, file_size, chunks_downloaded):
        metadata_path = self.get_chunk_metadata_path(file_path)
        metadata = {
            "file_size": file_size,
            "chunks_downloaded": chunks_downloaded,
        }
        try:
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
            self.plugin.log_debug(f"Chunk metadata saved: {metadata_path}")
        except IOError as exc:
            self.plugin.log_warning(f"Failed to save chunk metadata: {exc}")

    def load_chunk_metadata(self, file_path=None):
        metadata_path = self.get_chunk_metadata_path(file_path)
        if not exists(metadata_path):
            return None

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            if isinstance(metadata, dict):
                metadata["chunks_downloaded"] = {
                    int(key): value
                    for key, value in metadata.get("chunks_downloaded", {}).items()
                }
            self.plugin.log_debug(f"Chunk metadata loaded: {metadata_path}")
            return metadata
        except (IOError, json.JSONDecodeError) as exc:
            self.plugin.log_warning(f"Failed to load chunk metadata: {exc}")
            return None

    def initialize_progress(self):
        self.aggregated_dl = AggregatedDownload(
            self.file_size,
            master_browser=self.plugin.req,
            progress_notify=self.plugin.pyfile.set_progress,
        )
        self.aggregated_dl.set_persisted_bytes(sum(self.chunks_downloaded.values()))
        if self.plugin.req:
            self.plugin.req.dl = self.aggregated_dl
        return self.aggregated_dl

    def update_progress(self):
        """Update combined progress from all worker browsers."""
        if self.aggregated_dl:
            self.aggregated_dl.update_progress()

    def download_chunk(self, browser, url, filename, chunk_index, start_pos, end_pos):
        """Download a chunk using the per-thread browser."""
        chunk_file = f"{filename}.chunk{chunk_index}"
        chunk_file_partial = f"{filename}.chunk{chunk_index}.chunk0"
        resume_pos = 0
        if exists(chunk_file_partial):
            resume_pos = os.path.getsize(chunk_file_partial)
            self.plugin.log_debug(f"Resuming chunk {chunk_index} from byte {resume_pos}")

        url = f"{url}/{start_pos + resume_pos}-{end_pos}"

        if self.plugin.pyfile.abort:
            self.plugin.log_info(f"Chunk {chunk_index} aborted before start")
            raise Abort

        # Use per-thread browser to download
        browser.http_download(
            url,
            chunk_file,
            resume=resume_pos > 0,
            chunks=1,
        )

        bytes_downloaded = os.path.getsize(chunk_file)
        self.plugin.log_debug(f"Chunk {chunk_index} completed: {bytes_downloaded} bytes")

        return chunk_index, bytes_downloaded

    def merge_chunks(self):
        self.plugin.log_info(f"Merging {self.chunk_count} chunks into {self.filename}")
        self.plugin.pyfile.set_custom_status("merging")
        self.plugin.pyfile.set_progress(0)

        bytes_merged = 0
        buffer_size = 1024 * 1024  # 1 MB buffer for efficient I/O
        try:
            with open(self.filename, "wb") as final_file:
                for chunk_index in range(self.chunk_count):
                    chunk_file = f"{self.filename}.chunk{chunk_index}"
                    if not exists(chunk_file):
                        self.plugin.fail(f"Missing chunk file: {chunk_file}")

                    with open(chunk_file, "rb") as chunk_fp:
                        # Use buffered reading for efficient I/O with large files
                        while True:
                            chunk_data = chunk_fp.read(buffer_size)
                            if not chunk_data:
                                break
                            final_file.write(chunk_data)
                            bytes_merged += len(chunk_data)

                    # Update progress
                    if self.file_size > 0:
                        self.plugin.pyfile.set_progress((bytes_merged * 100) // self.file_size)

                    # Clean up chunk file
                    try:
                        os.remove(chunk_file)
                    except OSError:
                        pass

            # Validate final file size
            final_size = os.path.getsize(self.filename)
            if final_size != self.file_size:
                self.plugin.log_warning(
                    f"Final file size mismatch: {final_size} != {self.file_size}"
                )

            # Clean up metadata
            metadata_path = self.get_chunk_metadata_path(self.filename)
            if exists(metadata_path):
                try:
                    os.remove(metadata_path)
                except OSError:
                    pass

            self.plugin.log_info("Chunks merged successfully")

        except IOError as exc:
            self.plugin.fail(f"Error merging chunks: {exc}")

        self.plugin.pyfile.set_progress(100)

    @threaded
    def download_worker(self, queue, lock, thread=None):
        """Worker thread: download chunks with a browser owned by AggregatedDownload."""
        browser = self.aggregated_dl.register_browser()
        try:
            while True:
                if self.stop_requests:
                    # drain the queue
                    while True:
                        try:
                            queue.get_nowait()
                        except Empty:
                            break
                        else:
                            queue.task_done()
                    break

                try:
                    item = queue.get(block=False)
                except Empty:
                    break

                chunk_index, start_pos, end_pos = item

                try:
                    if self.plugin.pyfile.abort or self.aggregated_dl.abort:
                        self.stop_requests = True
                        continue

                    res_index, bytes_downloaded = self.download_chunk(
                        browser, self.url, self.filename, chunk_index, start_pos, end_pos
                    )

                    with lock:
                        self.chunks_downloaded[res_index] = bytes_downloaded
                        self.aggregated_dl.set_persisted_bytes(
                            sum(self.chunks_downloaded.values())
                        )
                        self.update_progress()
                        self.save_chunk_metadata(
                            self.filename, self.file_size, self.chunks_downloaded
                        )

                except Abort:
                    self.exception_holder = Abort()
                    self.stop_requests = True
                    continue

                except pycurl.error as exc:
                    code = exc.args[0]
                    if code == pycurl.E_RECV_ERROR:
                        self.plugin.log_warning(
                            "Mega chunk download hit over-quota/connection reset; stopping remaining workers"
                        )
                        self.exception_holder = OverQuotaError()
                        self.stop_requests = True
                        continue

                    raise

                except Exception as exc:
                    if self.exception_holder is None:
                        self.exception_holder = exc
                        self.stop_requests = True
                        continue

                finally:
                    queue.task_done()
        finally:
            self.aggregated_dl.unregister_browser()

    def run(self):
        metadata = self.load_chunk_metadata()
        self.chunks_downloaded = metadata.get("chunks_downloaded", {}) if metadata else {}
        self.stop_requests = False
        self.exception_holder = None

        dl_chunks = self.pyload.config.get("download", "chunks")
        chunk_limit = self.plugin.chunk_limit or -1

        if -1 in (dl_chunks, chunk_limit):
            max_workers = max(dl_chunks, chunk_limit)
        else:
            max_workers = min(dl_chunks, chunk_limit)

        self.initialize_progress()
        self.plugin.log_info(f"Starting chunked download: {self.chunk_count} chunks of {self.chunk_size // (1024 * 1024)} MB using {max_workers} download workers")

        # Build a queue of pending chunks (skip already completed chunks)
        pending_queue = Queue()
        for chunk_index, start_pos, end_pos in self.chunks_info:
            if chunk_index in self.chunks_downloaded:
                expected_bytes = end_pos - start_pos + 1
                if self.chunks_downloaded[chunk_index] >= expected_bytes:
                    self.plugin.log_debug(f"Chunk {chunk_index} already downloaded")
                    continue
            pending_queue.put((chunk_index, start_pos, end_pos))

        lock = threading.Lock()

        workers = []
        for _ in range(min(max_workers, pending_queue.qsize() or 1)):
            th = self.download_worker(pending_queue, lock)
            workers.append(th)

        try:
            self.plugin.pyfile.set_status("downloading")

            # Wait until all tasks processed
            pending_queue.join()

            if self.plugin.pyfile.abort:
                raise Abort

            if self.exception_holder is not None:
                raise self.exception_holder

        except Abort:
            self.plugin.log_info("Chunked download aborted")
            # nothing to cancel explicitly, workers will see abort flag
            self.save_chunk_metadata(self.filename, self.file_size, self.chunks_downloaded)
            raise

        except Exception as exc:
            self.plugin.log_error(f"Error during chunked download: {exc}")
            self.save_chunk_metadata(self.filename, self.file_size, self.chunks_downloaded)
            raise

        return self.chunks_downloaded


class MegaCoNz(BaseDownloader):
    __name__ = "MegaCoNz"
    __type__ = "downloader"
    __version__ = "0.61"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?mega(?:\.co)?\.nz/(?:file/(?P<ID1>[\w^_]+)#(?P<K1>[\w\-,=]+)|folder/(?P<ID2>[\w^_]+)#(?P<K2>[\w\-,=]+)/file/(?P<NID>[\w^_]+)|#!(?P<ID3>[\w^_]+)!(?P<K3>[\w\-,=]+))"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_chunked", "bool", "Use chunked downloads", True),
        ("chunk_size", "int", "Chunk size in MB (16 MB recommended)", 16),
    ]

    __description__ = """Mega.co.nz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "ranan@pyload.net"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT}yahoo[DOT]com"),
    ]

    FILE_SUFFIX = ".crypted"
    CHUNK_METADATA_SUFFIX = ".mega_chunks"
    DEFAULT_CHUNK_SIZE = 16 * 1024 * 1024  # 16 MB

    def setup(self):
        self.chunk_limit = -1

    def decrypt_file(self, key):
        """
        Decrypts and verifies checksum to the file at 'last_download'.
        """
        k, iv, meta_mac = MegaCrypto.get_cipher_key(key)
        cipher = Cipher(
            algorithms.AES(MegaCrypto.a32_to_bytes(k)),
            modes.CTR(MegaCrypto.a32_to_bytes(iv)),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()

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

        if checksum_activated and check_checksum:
            cbc_mac = MegaCrypto.Checksum(key)

        progress = 0
        for chunk_start, chunk_size in MegaCrypto.get_chunks(encrypted_size):
            buf = f.read(chunk_size)
            if not buf:
                break

            chunk = decryptor.update(buf)
            df.write(chunk)

            progress += chunk_size
            self.pyfile.set_progress((100 * progress) // encrypted_size)

            if checksum_activated and check_checksum:
                cbc_mac.update(chunk)

        df.write(decryptor.finalize())
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

        self.last_download = file_decrypted

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

    def download_chunked(self, url, filename, file_size):
        """
        Download file using chunks with Mega's custom URL format and resume support.

        :param url: Download URL from Mega API
        :param filename: Full path to save crypted file to
        :param file_size: Total file size in bytes
        """
        chunk_size_mb = self.config.get("chunk_size", 16)

        chunked_download = MegaChunkedDownload(self, url, filename, file_size, chunk_size_mb)
        chunked_download.run()
        chunked_download.merge_chunks()

    def find_root_node(self, res_f):
        """
        Build a tree of the folder nodes. Return the handle of the top-most node.
        """
        tree = {}
        for node in res_f:
            if node['t'] == 1 and node['h'] and node['p']:
                tree[node['h']] = node['p']

        for key, val in tree.items():
            if val not in tree:
                return key

    def build_key_dict(self, node_k):
        """
        Take a node's k value, and produce a dictionary.
        """
        dict = {}
        node_k = node_k.split('/')
        for key_data in node_k:
            h = key_data[:key_data.index(':')]
            l = key_data[key_data.index(':') + 1:]
            dict[h] = l

        return dict

    def calc_overquota_wait(self, res_uq):
        transfer_history = res_uq.get('tah', [])
        total_used = sum(transfer_history)
        base_transfer = res_uq.get('bt', 0)
        remaining = res_uq.get('tar', 0)
        is_overquota = total_used >= base_transfer or remaining <= 0
        if not is_overquota:
            time_left = 0
        else:
            add = 1
            time_left = 3600 - (base_transfer % 3600)

            for value in transfer_history:
                if value:
                    add = 0
                elif add:
                    time_left += 3600

        return time_left

    def process(self, pyfile):
        node_id = self.info['pattern']['NID']
        public = node_id in ("", None)
        id = self.info['pattern']['ID1'] or self.info['pattern']['ID2'] or self.info['pattern']['ID3']
        key = self.info['pattern']['K1'] or self.info['pattern']['K2'] or self.info['pattern']['K3']

        self.log_debug(
            "ID: {},".format(id),
            "Key: {}".format(key),
            "Type: {}".format('public' if public else 'node'),
            "Owner: {}".format(node_id)
        )

        mega = MegaClient(self, id)

        master_key = MegaCrypto.base64_to_a32(key)
        if not public:
            #: F is for requesting folder listing (kind like a `ls` command)
            res = mega.api_request(a="f", c=1, r=1, ca=1, ssl=1)
            if isinstance(res, int):
                mega.check_error(res)
            elif isinstance(res, dict) and 'e' in res:
                mega.check_error(res['e'])

            root_handle = self.find_root_node(res['f'])
            self.log_debug("Root Folder Handle: {}".format(root_handle))
            for node in res['f']:
                if node['t'] == 0 and ":" in node["k"] and node['h'] == node_id:
                    keys = self.build_key_dict(node['k'])
                    file_key = keys.get(root_handle)
                    if not file_key:
                        self.log_error(self._("Root folder handle not found in file keys"))
                        self.fail(self._("Root folder handle not found in file keys"))

                    master_key = MegaCrypto.decrypt_key(file_key, master_key)
                    break

            else:
                self.offline()

        if len(master_key) != 8:
            self.log_error(self._("Invalid key length"))
            self.fail(self._("Invalid key length"))

        #: G is for requesting a download url
        if public:
            res = mega.api_request(a="g", g=1, p=id, ssl=1)
        else:
            res = mega.api_request(a="g", g=1, n=node_id, ssl=1)

        if isinstance(res, int):
            mega.check_error(res)
        elif isinstance(res, dict) and "e" in res:
            mega.check_error(res["e"])

        attr = MegaCrypto.decrypt_attr(res["at"], master_key)
        if not attr:
            self.fail(self._("Decryption failed"))

        self.log_debug(f"Decrypted Attr: {attr}")

        name = attr["n"]

        self.check_exists(name)

        pyfile.name = name + self.FILE_SUFFIX
        pyfile.size = res["s"]

        time_left = res.get("tl", 0)
        if time_left:
            self.log_warning(self._("Free download limit reached"))
            self.retry(wait=time_left, msg=self._("Free download limit reached"))

        # Use chunked download if enabled, otherwise use standard download
        use_chunked = self.config.get("use_chunked", default=True, plugin="MegaCoNz")

        try:
            if use_chunked:
                # Get the target filename for the crypted file
                dl_root_folder = self.pyload.config.get("general", "storage_folder")
                dl_package_folder = self.pyfile.package().folder if self.pyload.config.get("general", "folder_per_package") else ""
                dl_filename = fs.safejoin(dl_root_folder, dl_package_folder, self.pyfile.name)

                # Create directory if needed
                os.makedirs(os.path.dirname(dl_filename), exist_ok=True)

                self.download_chunked(res["g"], dl_filename, res["s"])
                self.last_download = dl_filename
            else:
                self.download(res["g"], disposition=False)

        except BadHeader as exc:
            if exc.code == 509:
                self.fail(self._("Bandwidth Limit Exceeded"))

            else:
                raise

        except OverQuotaError:
            if not self.premium:
                res = mega.api_request(a="uq", xfer=1, pro=1)  #: user quota details
                if isinstance(res, int):
                    mega.check_error(res)
                elif isinstance(res, dict) and "e" in res:
                    mega.check_error(res["e"])

                wait_time = self.calc_overquota_wait(res)
                if wait_time:
                    self.log_warning(self._("Free Bandwidth limit reached, waiting {}").format(format.time(wait_time)))
                    self.retry(wait=wait_time, msg=self._("Free Bandwidth limit reached"))

            else:
                self.fail(self._("Premium download failed, connection reset"))

        self.decrypt_file(master_key)

        #: Everything is finished and final name can be set
        pyfile.name = name
